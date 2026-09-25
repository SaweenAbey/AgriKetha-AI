import time
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.core.logging_config import logger
from app.core.database import db_state
from collections import defaultdict
from threading import Lock


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs incoming requests with HTTP method, path,
    client IP, response status code, and process time in milliseconds.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        url_path = request.url.path

        try:
            response = await call_next(request)
            process_time = (time.perf_counter() - start_time) * 1000
            status_code = response.status_code

            # Log formatted request info
            log_msg = f"{client_ip} | {method} {url_path} | Status: {status_code} | {process_time:.2f}ms"
            if status_code >= 500:
                logger.error(log_msg)
            elif status_code >= 400:
                logger.warning(log_msg)
            else:
                logger.info(log_msg)

            response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
            return response
        except Exception as exc:
            process_time = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"{client_ip} | {method} {url_path} | Exception: {exc} | {process_time:.2f}ms",
                exc_info=True
            )
            raise exc

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds standard defensive HTTP response headers to every API response."""

    HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
        "Cache-Control": "no-store",
    }

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        for name, value in self.HEADERS.items():
            response.headers.setdefault(name, value)
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiter for the orchestrator endpoint.

    Limits each client IP to 10 requests per 60 seconds.
    """

    def __init__(self, app, max_requests: int = 10, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
        self.lock = Lock()

    async def dispatch(self, request: Request, call_next) -> Response:
        # Apply rate limiting only to the Agent 4 orchestrator endpoint
        if request.url.path.endswith("/orchestrator/query"):
            client_ip = request.client.host if request.client else "unknown"
            current_time = time.time()

            with self.lock:
                request_times = self.requests[client_ip]

                # Remove requests outside the current time window
                request_times[:] = [
                    request_time
                    for request_time in request_times
                    if current_time - request_time < self.window_seconds
                ]

                if len(request_times) >= self.max_requests:
                    logger.warning(
                        "Rate limit exceeded | IP: %s | Path: %s",
                        client_ip,
                        request.url.path,
                    )

                    return Response(
                        content='{"detail":"Rate limit exceeded. Please try again later."}',
                        status_code=429,
                        media_type="application/json",
                    )

                request_times.append(current_time)

        return await call_next(request)

async def record_audit_log(
    action: str,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
    role: Optional[str] = None,
    status: str = "SUCCESS",
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
):
    """
    Persists security and administrative activity events into MongoDB `audit_logs` collection.
    """
    if db_state.db is None:
        return

    try:
        log_entry = {
            "action": action,
            "user_id": user_id,
            "user_email": user_email,
            "role": role,
            "status": status,
            "details": details or {},
            "ip_address": ip_address,
            "created_at": datetime.now(timezone.utc)
        }
        await db_state.db.audit_logs.insert_one(log_entry)
    except Exception as e:
        logger.error("Failed to write to audit log in MongoDB: %s", e)

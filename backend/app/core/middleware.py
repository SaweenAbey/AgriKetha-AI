import time
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.core.logging_config import logger
from app.core.database import db_state


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

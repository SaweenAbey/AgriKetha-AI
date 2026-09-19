import httpx
from typing import Any, Optional

from app.core.config import settings
from app.core.logging_config import logger


class AgentClientError(Exception):
    """Raised when an AI agent cannot be reached or returns an error."""


# Fast connect timeout so offline services fail over instantly
CLIENT_TIMEOUT = httpx.Timeout(connect=1.5, read=30.0, write=15.0, pool=3.0)


async def call_query_agent(question: str) -> dict[str, Any]:
    """
    Call Agent 2 (Query/NLP Agent).

    Agent 2 endpoint:
        POST /analyze
    """
    candidate_urls = [settings.QUERY_AGENT_URL, "http://127.0.0.1:8001", "http://localhost:8001"]
    seen = set()
    urls = [u for u in candidate_urls if not (u in seen or seen.add(u))]

    last_error = None
    for base_url in urls:
        url = f"{base_url.rstrip('/')}/analyze"
        try:
            async with httpx.AsyncClient(timeout=CLIENT_TIMEOUT) as client:
                response = await client.post(
                    url,
                    json={"question": question},
                )
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_error = exc
            continue

    raise AgentClientError(f"Query Agent request failed: {last_error}")


async def call_vision_agent(
    image_bytes: bytes,
    filename: str,
    content_type: Optional[str] = None,
) -> dict[str, Any]:
    """
    Call Agent 1 (Vision Agent).

    Agent 1 endpoint:
        POST /agent/image/analyze
    """
    candidate_urls = [settings.VISION_AGENT_URL, "http://127.0.0.1:8002", "http://localhost:8002"]
    seen = set()
    urls = [u for u in candidate_urls if not (u in seen or seen.add(u))]

    files = {
        "file": (
            filename,
            image_bytes,
            content_type or "application/octet-stream",
        )
    }

    last_error = None
    for base_url in urls:
        url = f"{base_url.rstrip('/')}/agent/image/analyze"
        try:
            async with httpx.AsyncClient(timeout=CLIENT_TIMEOUT) as client:
                response = await client.post(
                    url,
                    files=files,
                )
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_error = exc
            continue

    raise AgentClientError(f"Vision Agent request failed: {last_error}")


async def call_research_agent(
    query: str,
    crop: Optional[str] = None,
    topic: Optional[str] = None,
    top_k: int = 5,
) -> dict[str, Any]:
    """
    Call Agent 3 (Agricultural Research/RAG Agent).

    Agent 3 endpoint:
        POST /agent/retrieve
    """
    candidate_urls = [
        settings.RESEARCH_AGENT_URL,
        "http://127.0.0.1:8004",
        "http://localhost:8004",
        "http://127.0.0.1:8003",
        "http://localhost:8003",
    ]
    seen = set()
    urls = [u for u in candidate_urls if not (u in seen or seen.add(u))]

    payload = {
        "query": query,
        "crop": crop,
        "topic": topic,
        "top_k": top_k,
    }

    last_error = None
    for base_url in urls:
        url = f"{base_url.rstrip('/')}/agent/retrieve"
        try:
            async with httpx.AsyncClient(timeout=CLIENT_TIMEOUT) as client:
                response = await client.post(
                    url,
                    json=payload,
                )
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_error = exc
            continue

    raise AgentClientError(f"Research Agent request failed: {last_error}")

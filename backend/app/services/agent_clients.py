import httpx
from typing import Any, Optional

from app.core.config import settings


class AgentClientError(Exception):
    """Raised when an AI agent cannot be reached or returns an error."""


async def call_query_agent(question: str) -> dict[str, Any]:
    """
    Call Agent 2 (Query/NLP Agent).

    Agent 2 endpoint:
        POST /analyze

    Request:
        {"question": "..."}
    """

    url = f"{settings.QUERY_AGENT_URL}/analyze"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url,
                json={"question": question},
            )

        response.raise_for_status()
        return response.json()

    except httpx.HTTPError as exc:
        raise AgentClientError(
            f"Query Agent request failed: {exc}"
        ) from exc


async def call_vision_agent(
    image_bytes: bytes,
    filename: str,
    content_type: Optional[str] = None,
) -> dict[str, Any]:
    """
    Call Agent 1 (Vision Agent).

    Agent 1 endpoint:
        POST /agent/image/analyze

    Request:
        multipart/form-data with field 'file'
    """

    url = f"{settings.VISION_AGENT_URL}/agent/image/analyze"

    try:
        files = {
            "file": (
                filename,
                image_bytes,
                content_type or "application/octet-stream",
            )
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                files=files,
            )

        response.raise_for_status()
        return response.json()

    except httpx.HTTPError as exc:
        raise AgentClientError(
            f"Vision Agent request failed: {exc}"
        ) from exc


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

    url = f"{settings.RESEARCH_AGENT_URL}/agent/retrieve"

    payload = {
        "query": query,
        "crop": crop,
        "topic": topic,
        "top_k": top_k,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                json=payload,
            )

        response.raise_for_status()
        return response.json()

    except httpx.HTTPError as exc:
        raise AgentClientError(
            f"Research Agent request failed: {exc}"
        ) from exc
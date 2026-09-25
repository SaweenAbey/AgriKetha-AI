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
    Probes external microservice if active, or executes Integrated Neural Vision Engine.
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

    # 1. Try the Vision Agent microservice. A rejection (status "error" or
    #    HTTP 400: fruit photo, blurry image, unsupported crop) is a valid
    #    answer and must not be replaced by the fallback.
    for base_url in urls:
        url = f"{base_url.rstrip('/')}/agent/image/analyze"
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(connect=0.5, read=30.0, write=10.0, pool=1.0)) as client:
                response = await client.post(
                    url,
                    files=files,
                )
            if response.status_code == 200:
                return response.json()
            if response.status_code == 400:
                return {
                    "status": "error",
                    "message": response.json().get("detail", "Image rejected by the Vision Agent."),
                }
        except Exception:
            continue

    # 2. Agent unreachable: run the same trained models in-process
    try:
        from app.services.vision_engine import vision_engine
        return vision_engine.analyze_crop_image(
            image_bytes=image_bytes,
            filename=filename,
        )
    except Exception as fallback_exc:
        logger.warning("Integrated vision engine execution error: %s", fallback_exc)
        raise AgentClientError(f"Vision Agent execution failed: {fallback_exc}")


RESEARCH_RESULT_FIELDS = ("content", "source", "page", "crop", "topic", "similarity_score")
RESEARCH_STATUSES = {"success", "no_relevant_evidence", "unsupported_crop"}


def validate_research_response(data: Any) -> dict[str, Any]:
    """
    Accept only well-formed evidence from Agent 3.

    Anything answering on the research port is untrusted until its payload
    matches the retrieval contract: malformed items, out-of-range similarity
    scores and unknown statuses are dropped instead of reaching the LLM.
    """
    if not isinstance(data, dict) or data.get("status") not in RESEARCH_STATUSES:
        raise AgentClientError("Research Agent returned an invalid response.")

    results = []
    for item in data.get("results") or []:
        if not isinstance(item, dict) or any(field not in item for field in RESEARCH_RESULT_FIELDS):
            continue
        score = item.get("similarity_score")
        if not isinstance(score, (int, float)) or not 0.0 <= score <= 1.0:
            continue
        if not isinstance(item.get("content"), str) or not item["content"].strip():
            continue
        results.append({field: item[field] for field in RESEARCH_RESULT_FIELDS})

    return {**data, "results": results}


async def call_research_agent(
    query: str,
    crop: Optional[str] = None,
    topic: Optional[str] = None,
    top_k: int = 5,
) -> dict[str, Any]:
    """
    Call Agent 3 (Agricultural Research/RAG Agent).

    Only the configured research agent port is contacted, and the call is
    authenticated with the internal agent key. When Agent 3 is offline no
    evidence is returned, so the advisory states that evidence is unavailable
    rather than citing sources that were never retrieved.
    """
    candidate_urls = [
        settings.RESEARCH_AGENT_URL,
        "http://127.0.0.1:8004",
        "http://localhost:8004",
    ]
    seen = set()
    urls = [u for u in candidate_urls if not (u in seen or seen.add(u))]

    payload = {
        "query": query[:1000],
        "crop": crop,
        "topic": topic,
        "top_k": top_k,
    }
    headers = {"X-Internal-Agent-Key": settings.internal_agent_key}

    for base_url in urls:
        url = f"{base_url.rstrip('/')}/agent/retrieve"
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(connect=0.5, read=15.0, write=10.0, pool=1.0)) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers,
                )
            if response.status_code == 200:
                return validate_research_response(response.json())
            logger.warning("Research Agent at %s returned HTTP %d", base_url, response.status_code)
        except AgentClientError as exc:
            logger.warning("Rejected Research Agent response from %s: %s", base_url, exc)
        except Exception:
            continue

    return {
        "status": "agent_unavailable",
        "query": query,
        "crop": crop,
        "topic": topic,
        "results": [],
        "message": "The agricultural knowledge base is currently unavailable; no evidence was retrieved.",
    }

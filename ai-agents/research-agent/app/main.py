"""FastAPI entry point for Agent 3."""

from fastapi import Depends, FastAPI, Header, HTTPException, status

from .config import INTERNAL_AGENT_KEY
from .retriever import AgriculturalRetriever
from .schemas import RetrievalRequest, RetrievalResponse
from .security import is_valid_agent_key


def require_internal_key(
    x_internal_agent_key: str | None = Header(default=None),
) -> None:
    """Only the backend orchestrator, which holds the shared key, may retrieve."""
    if not is_valid_agent_key(x_internal_agent_key, INTERNAL_AGENT_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid internal agent key.",
        )


app = FastAPI(
    title="AgriKetha Agricultural Knowledge Retrieval Agent",
    version="1.0.0",
)
retriever: AgriculturalRetriever | None = None


@app.on_event("startup")
def load_retriever() -> None:
    global retriever
    retriever = AgriculturalRetriever()


@app.get("/agent/health")
def health() -> dict[str, str | bool]:
    return {
        "status": "healthy",
        "agent": "research-agent",
        "vector_store_loaded": bool(retriever and retriever.loaded),
    }


@app.post(
    "/agent/retrieve",
    response_model=RetrievalResponse,
    dependencies=[Depends(require_internal_key)],
)
def retrieve(request: RetrievalRequest) -> RetrievalResponse:
    if retriever is None:
        return RetrievalResponse(
            status="no_relevant_evidence",
            query=request.query,
            results=[],
            message="The research agent has not finished starting up yet.",
            requested_crop=request.crop,
            available_crops=[],
        )

    outcome = retriever.retrieve(request.query, request.crop, request.topic, request.top_k)
    return RetrievalResponse(
        status=outcome.status,
        query=request.query,
        results=outcome.results,
        message=outcome.message,
        requested_crop=outcome.requested_crop,
        available_crops=outcome.available_crops,
    )
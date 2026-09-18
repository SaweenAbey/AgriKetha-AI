"""FastAPI entry point for Agent 3."""

from fastapi import FastAPI

from .retriever import AgriculturalRetriever
from .schemas import RetrievalRequest, RetrievalResponse


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


@app.post("/agent/retrieve", response_model=RetrievalResponse)
def retrieve(request: RetrievalRequest) -> RetrievalResponse:
    results = (
        retriever.retrieve(request.query, request.crop, request.topic, request.top_k)
        if retriever
        else []
    )
    return RetrievalResponse(
        status="success" if results else "no_relevant_evidence",
        query=request.query,
        results=results,
    )
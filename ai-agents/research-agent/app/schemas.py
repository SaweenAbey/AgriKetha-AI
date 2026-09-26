"""Request and response models for Agent 3."""

from typing import Literal

from pydantic import BaseModel, Field

from .config import DEFAULT_TOP_K, MAX_QUERY_CHARS, MAX_TOP_K


class RetrievalRequest(BaseModel):
    query: str = Field(min_length=1, max_length=MAX_QUERY_CHARS)
    crop: str | None = Field(default=None, max_length=40, pattern=r"^[A-Za-z _-]+$")
    topic: str | None = Field(default=None, max_length=40, pattern=r"^[A-Za-z _-]+$")
    top_k: int = Field(default=DEFAULT_TOP_K, ge=1, le=MAX_TOP_K)


class EvidenceResult(BaseModel):
    content: str
    source: str
    page: int
    crop: str
    topic: str
    similarity_score: float


class RetrievalResponse(BaseModel):
    status: Literal["success", "no_relevant_evidence", "unsupported_crop"]
    query: str
    results: list[EvidenceResult]
    message: str | None = None
    requested_crop: str | None = None
    available_crops: list[str] = Field(default_factory=list)

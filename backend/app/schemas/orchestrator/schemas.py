from typing import Any, List, Optional
from pydantic import BaseModel, Field


class OrchestratorRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=800,
        description="Farmer's agricultural question."
    )


class AgentActivity(BaseModel):
    agent: str
    status: str
    details: Optional[str] = None


class SourceReference(BaseModel):
    source: str
    page: Optional[int] = None
    similarity_score: Optional[float] = None


class OrchestratorResponse(BaseModel):
    success: bool
    session_id: str
    question: str

    detected_language: Optional[str] = None
    crop: Optional[str] = None
    intent: Optional[str] = None

    advisory: str

    vision_result: Optional[dict[str, Any]] = None
    evidence: List[dict[str, Any]] = []
    sources: List[SourceReference] = []

    agent_activity: List[AgentActivity] = []

    safety_note: Optional[str] = None
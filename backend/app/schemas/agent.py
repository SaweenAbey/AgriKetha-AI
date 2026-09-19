from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class QueryAgentRequest(BaseModel):
    question: str = Field(
        ...,
        description="The natural language farming question or crop symptom description.",
        examples=["My tomato leaves are turning yellow with dark brown spots."]
    )
    input_mode: Optional[str] = Field("text", description="'text' or 'voice'")
    auto_triggered: Optional[bool] = Field(False, description="Whether the request was automatically fired from speech recognition.")
    language: Optional[str] = Field("en", description="Language code e.g. 'en', 'si', 'ta'")


class NLPAnalysisResultSchema(BaseModel):
    crop: Optional[str] = None
    symptoms: List[str] = []
    intent: str = "general agriculture"


class QueryAgentResponse(BaseModel):
    id: Optional[str] = None
    question: str
    input_mode: Optional[str] = "text"
    auto_triggered: Optional[bool] = False
    agent_status: str
    agent_response: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

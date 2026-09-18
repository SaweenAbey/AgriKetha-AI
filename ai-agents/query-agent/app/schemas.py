from pydantic import BaseModel, Field
from typing import List, Optional, Any


class QueryRequest(BaseModel):
    question: str = Field(
        ..., 
        description="The question or description of crop symptoms asked by the farmer.",
        examples=["My tomato leaves are becoming yellow and I see brown spots."]
    )


class NLPAnalysisResult(BaseModel):
    crop: Optional[str] = Field(
        None, 
        description="The extracted and normalized crop name (e.g. tomato, rice)."
    )
    symptoms: List[str] = Field(
        default=[], 
        description="A list of canonical symptoms extracted from the query."
    )
    fertilizer_details: List[str] = Field(
        default=[],
        description="A list of canonical fertilizer or nutrient terms extracted from the query."
    )
    machinery_details: List[str] = Field(
        default=[],
        description="A list of machinery or machine operation terms extracted from the query."
    )
    intent: str = Field(
        ..., 
        description="The classified user intent (e.g. disease diagnosis, market information)."
    )


class QueryResponse(BaseModel):
    success: bool = Field(..., description="Indicates if the query was processed successfully.")
    agent: str = Field("query-analysis-agent", description="The name of the processing agent.")
    question: str = Field(..., description="The original farmer query.")
    detected_language: str = Field("en", description="The detected language of the query (e.g. en, si, singlish).")
    translated_question: Optional[str] = Field(None, description="The translated English version of the query if not in English.")
    agent_1_result: NLPAnalysisResult = Field(..., description="The structured entity and intent extraction results.")
    agent_2_connected: bool = Field(..., description="Boolean indicating if Agent 2 was reachable.")
    agent_2_result: Any = Field(..., description="The response dictionary returned from Agent 2, or error fallback.")


from pydantic import BaseModel
from typing import List, Optional

class DiseasePrediction(BaseModel):
    disease: str
    confidence: float

class VisionResponse(BaseModel):
    status: str  # "success" or "error"
    crop: Optional[str] = None
    prediction: Optional[str] = None
    confidence: Optional[float] = None
    severity_percentage: Optional[float] = None
    severity_level: Optional[str] = None  # "Mild", "Moderate", "Severe"
    gradcam_base64: Optional[str] = None
    alternatives: List[DiseasePrediction] = []
    message: Optional[str] = None
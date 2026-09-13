from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.farm import CropItem


class CropCreate(BaseModel):
    name: str
    variety: Optional[str] = None
    planted_date: Optional[str] = None
    acres_planted: Optional[float] = 1.0
    stage: Optional[str] = "growing"


class FarmCreate(BaseModel):
    farm_name: Optional[str] = "My Farm"
    district: str
    area_or_village: Optional[str] = None
    total_land_size_acres: Optional[float] = 1.0
    soil_type: Optional[str] = None
    irrigation_source: Optional[str] = "Rainfed"
    crops: List[CropItem] = []


class FarmUpdate(BaseModel):
    farm_name: Optional[str] = None
    district: Optional[str] = None
    area_or_village: Optional[str] = None
    total_land_size_acres: Optional[float] = None
    soil_type: Optional[str] = None
    irrigation_source: Optional[str] = None


class FarmOut(BaseModel):
    id: str
    user_id: str
    farm_name: str
    district: str
    area_or_village: Optional[str] = None
    total_land_size_acres: float
    soil_type: Optional[str] = None
    irrigation_source: str
    crops: List[CropItem] = []
    created_at: datetime
    updated_at: datetime

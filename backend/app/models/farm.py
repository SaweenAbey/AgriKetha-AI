from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field


class CropItem(BaseModel):
    name: str
    variety: Optional[str] = None
    planted_date: Optional[str] = None
    acres_planted: Optional[float] = None
    stage: Optional[str] = "growing"  # e.g., seedling, vegetative, flowering, harvesting


class FarmInDB(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    farm_name: Optional[str] = "My Farm"
    district: str
    area_or_village: Optional[str] = None
    total_land_size_acres: Optional[float] = 1.0
    soil_type: Optional[str] = None
    irrigation_source: Optional[str] = "Rainfed"
    crops: List[CropItem] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        populate_by_name = True

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class AuditLogInDB(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    action: str
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    role: Optional[str] = None
    status: str = "SUCCESS"
    details: Dict[str, Any] = {}
    ip_address: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        populate_by_name = True

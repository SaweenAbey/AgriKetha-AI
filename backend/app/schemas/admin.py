from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from app.models.user import UserRole


class UserAdminUpdate(BaseModel):
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None


class AuditLogOut(BaseModel):
    id: str
    action: str
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    role: Optional[str] = None
    status: str
    details: Dict[str, Any] = {}
    ip_address: Optional[str] = None
    created_at: datetime


class SystemStatsOut(BaseModel):
    total_users: int
    total_farmers: int
    total_admins: int
    active_users: int
    total_farms_registered: int
    total_queries_recorded: int
    total_audit_events: int

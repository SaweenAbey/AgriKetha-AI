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


class AgentHealthInfo(BaseModel):
    id: str
    name: str
    name_si: Optional[str] = None
    status: str = "Healthy"
    uptime_pct: float = 99.9
    latency_ms: int = 120
    description: str


class SystemStatsOut(BaseModel):
    total_users: int
    total_customers: int
    total_farmers: int
    total_admins: int
    active_users: int
    pro_farmers: int
    free_farmers: int
    total_revenue: float
    total_farms_registered: int
    total_queries_recorded: int
    total_audit_events: int
    agents_health: List[AgentHealthInfo] = []


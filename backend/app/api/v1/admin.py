from datetime import datetime, timezone
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, Query
from bson import ObjectId
from app.core.database import get_db
from app.core.config import settings
from app.core.middleware import record_audit_log
from app.core.logging_config import logger
from app.schemas.user import UserOut
from app.schemas.admin import UserAdminUpdate, AuditLogOut, SystemStatsOut
from app.models.user import UserRole
from app.api.deps import require_admin

router = APIRouter(prefix="/admin", tags=["Admin Management"], dependencies=[Depends(require_admin)])


@router.get("/users", response_model=List[UserOut])
async def list_all_users(
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db = Depends(get_db)
):
    """
    [Admin Only] Retrieves paginated list of all users with optional filtering.
    """
    filter_query = {}
    if role:
        filter_query["role"] = role.value
    if is_active is not None:
        filter_query["is_active"] = is_active
    if search:
        filter_query["$or"] = [
            {"email": {"$regex": search, "$options": "i"}},
            {"full_name": {"$regex": search, "$options": "i"}},
            {"district": {"$regex": search, "$options": "i"}}
        ]

    cursor = db.users.find(filter_query).sort("created_at", -1).skip(skip).limit(limit)
    users = []
    async for u in cursor:
        u["id"] = str(u["_id"])
        users.append(UserOut(**u))
    return users


@router.patch("/users/{user_id}/status", response_model=UserOut)
async def update_user_status(
    user_id: str,
    is_active: bool = Query(..., description="Set active (True) or deactivated (False)"),
    current_admin: dict = Depends(require_admin),
    db = Depends(get_db)
):
    """
    [Admin Only] Activates or deactivates a user account.
    """
    try:
        obj_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format.")

    user = await db.users.find_one({"_id": obj_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Prevent admin from deactivating self
    if str(user["_id"]) == current_admin["id"] and not is_active:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own admin account.")

    await db.users.update_one(
        {"_id": obj_id},
        {"$set": {"is_active": is_active, "updated_at": datetime.now(timezone.utc)}}
    )

    await record_audit_log(
        action="ADMIN_UPDATE_USER_STATUS",
        user_id=current_admin["id"],
        user_email=current_admin["email"],
        role=current_admin["role"],
        status="SUCCESS",
        details={"target_user_id": user_id, "target_email": user["email"], "new_is_active": is_active}
    )

    updated_user = await db.users.find_one({"_id": obj_id})
    updated_user["id"] = str(updated_user["_id"])
    logger.info("Admin %s updated status for user %s to active=%s", current_admin["email"], user["email"], is_active)
    return UserOut(**updated_user)


@router.patch("/users/{user_id}/role", response_model=UserOut)
async def update_user_role(
    user_id: str,
    role: UserRole = Query(..., description="New role: 'farmer' or 'admin'"),
    current_admin: dict = Depends(require_admin),
    db = Depends(get_db)
):
    """
    [Admin Only] Changes a user's role (promote/demote).
    """
    try:
        obj_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format.")

    user = await db.users.find_one({"_id": obj_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if str(user["_id"]) == current_admin["id"] and role != UserRole.ADMIN:
        raise HTTPException(status_code=400, detail="You cannot demote your own admin account.")

    await db.users.update_one(
        {"_id": obj_id},
        {"$set": {"role": role.value, "updated_at": datetime.now(timezone.utc)}}
    )

    await record_audit_log(
        action="ADMIN_UPDATE_USER_ROLE",
        user_id=current_admin["id"],
        user_email=current_admin["email"],
        role=current_admin["role"],
        status="SUCCESS",
        details={"target_user_id": user_id, "target_email": user["email"], "new_role": role.value}
    )

    updated_user = await db.users.find_one({"_id": obj_id})
    updated_user["id"] = str(updated_user["_id"])
    logger.info("Admin %s updated role for user %s to role=%s", current_admin["email"], user["email"], role.value)
    return UserOut(**updated_user)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_admin: dict = Depends(require_admin),
    db = Depends(get_db)
):
    """
    [Admin Only] Deletes a user account and associated farm profile.
    """
    try:
        obj_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format.")

    if str(obj_id) == current_admin["id"]:
        raise HTTPException(status_code=400, detail="You cannot delete your own admin account.")

    user = await db.users.find_one({"_id": obj_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    await db.users.delete_one({"_id": obj_id})
    await db.farms.delete_one({"user_id": user_id})

    await record_audit_log(
        action="ADMIN_DELETE_USER",
        user_id=current_admin["id"],
        user_email=current_admin["email"],
        role=current_admin["role"],
        status="SUCCESS",
        details={"deleted_user_id": user_id, "deleted_email": user["email"]}
    )

    logger.info("Admin %s deleted user %s", current_admin["email"], user["email"])
    return {"message": f"User {user['email']} deleted successfully."}


@router.get("/audit-logs", response_model=List[AuditLogOut])
async def get_audit_logs(
    action: Optional[str] = None,
    user_email: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    db = Depends(get_db)
):
    """
    [Admin Only] View security and administrative activity logs stored in MongoDB.
    """
    query = {}
    if action:
        query["action"] = action
    if user_email:
        query["user_email"] = user_email
    if status_filter:
        query["status"] = status_filter

    cursor = db.audit_logs.find(query).sort("created_at", -1).limit(limit)
    logs = []
    async for item in cursor:
        item["id"] = str(item["_id"])
        logs.append(AuditLogOut(**item))
    return logs


@router.get("/stats", response_model=SystemStatsOut)
async def get_system_statistics(db = Depends(get_db)):
    """
    [Admin Only] High-level metrics for dashboard (total users, active farmers, etc.).
    """
    total_users = await db.users.count_documents({})
    total_farmers = await db.users.count_documents({"role": UserRole.FARMER.value})
    total_admins = await db.users.count_documents({"role": UserRole.ADMIN.value})
    active_users = await db.users.count_documents({"is_active": True})
    total_farms = await db.farms.count_documents({})
    total_queries = await db.farmer_queries.count_documents({})
    total_audit_events = await db.audit_logs.count_documents({})

    return SystemStatsOut(
        total_users=total_users,
        total_farmers=total_farmers,
        total_admins=total_admins,
        active_users=active_users,
        total_farms_registered=total_farms,
        total_queries_recorded=total_queries,
        total_audit_events=total_audit_events
    )


@router.get("/logs/file")
async def read_system_log_file(
    log_type: str = Query("app", description="'app' for general log, 'error' for error log"),
    lines: int = Query(100, ge=1, le=500)
):
    """
    [Admin Only] Reads the latest lines from the system log file on disk.
    """
    filename = "error.log" if log_type == "error" else "app.log"
    file_path = Path(settings.LOG_DIR) / filename

    if not file_path.exists():
        return {"filename": filename, "lines": [], "message": "Log file does not exist yet."}

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            all_lines = f.readlines()
            tail_lines = [l.strip() for l in all_lines[-lines:]]
        return {
            "filename": filename,
            "total_lines_returned": len(tail_lines),
            "lines": tail_lines
        }
    except Exception as e:
        logger.error("Error reading log file: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to read log file: {str(e)}")

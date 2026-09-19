from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash
from app.core.middleware import record_audit_log
from app.core.logging_config import logger
from app.schemas.user import UserOut, UserUpdate, ChangePasswordRequest, SubscriptionUpgradeRequest
from app.api.deps import get_current_user
from app.services.quota_service import QuotaService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/quota")
async def get_my_quota(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Returns the authenticated user's current daily usage, limits, and remaining allowance.
    Free users: 25 text queries, 5 images, 5 voice analyses per day.
    Subscription users: Unlimited.
    """
    user_id = ObjectId(current_user["id"])
    fresh_user = await db.users.find_one({"_id": user_id}) or current_user
    fresh_user["id"] = str(fresh_user["_id"]) if "_id" in fresh_user else current_user["id"]
    return await QuotaService.get_user_quota_status(db, fresh_user)


@router.post("/upgrade-subscription")
async def upgrade_subscription(
    req: SubscriptionUpgradeRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Upgrades or toggles the user's subscription tier between 'free' and 'premium' (unlimited).
    """
    target_plan = req.plan if req.plan in ["free", "premium", "pro"] else "premium"
    updated_quota = await QuotaService.set_user_subscription(db, current_user["id"], target_plan)

    await record_audit_log(
        action=f"SUBSCRIPTION_UPDATED_{target_plan.upper()}",
        user_id=current_user["id"],
        user_email=current_user["email"],
        role=current_user["role"],
        status="SUCCESS"
    )

    logger.info("User %s switched subscription plan to %s", current_user["email"], target_plan)
    return {
        "success": True,
        "message": f"Successfully updated subscription to {target_plan.capitalize()}.",
        "quota": updated_quota
    }


@router.put("/me", response_model=UserOut)
async def update_my_profile(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Updates the authenticated user's profile information.
    """
    update_data = {k: v for k, v in user_update.model_dump().items() if v is not None}
    if not update_data:
        return UserOut(**current_user)

    update_data["updated_at"] = datetime.now(timezone.utc)

    user_id = ObjectId(current_user["id"])
    await db.users.update_one({"_id": user_id}, {"$set": update_data})

    updated_user = await db.users.find_one({"_id": user_id})
    updated_user["id"] = str(updated_user["_id"])

    logger.info("User %s updated profile details", current_user["email"])
    return UserOut(**updated_user)


@router.put("/me/password")
async def change_my_password(
    pwd_in: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Changes the authenticated user's password.
    """
    user_id = ObjectId(current_user["id"])
    user = await db.users.find_one({"_id": user_id})

    if not verify_password(pwd_in.current_password, user.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password verification failed."
        )

    new_hash = get_password_hash(pwd_in.new_password)
    await db.users.update_one(
        {"_id": user_id},
        {"$set": {"hashed_password": new_hash, "updated_at": datetime.now(timezone.utc)}}
    )

    await record_audit_log(
        action="USER_PASSWORD_CHANGED",
        user_id=current_user["id"],
        user_email=current_user["email"],
        role=current_user["role"],
        status="SUCCESS"
    )

    logger.info("Password successfully changed for user %s", current_user["email"])
    return {"message": "Password changed successfully."}

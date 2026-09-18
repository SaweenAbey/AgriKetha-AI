from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash
from app.core.middleware import record_audit_log
from app.core.logging_config import logger
from app.schemas.user import UserOut, UserUpdate, ChangePasswordRequest
from app.api.deps import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


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

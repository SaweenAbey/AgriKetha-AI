from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import UserRole
from app.core.logging_config import logger

security_bearer = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
    db = Depends(get_db)
) -> dict:
    """
    Validates JWT access token, verifies subject in MongoDB,
    and returns current user document dictionary.
    """
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_type = payload.get("type")
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Expected access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception as e:
        logger.error("Error finding user by id %s: %s", user_id, e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or invalid token identifier",
        )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User belonging to this token no longer exists",
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your user account is currently deactivated. Please contact support/admin.",
        )

    # Convert ObjectId to string for easy schema serialization
    user["id"] = str(user["_id"])
    return user


def require_roles(allowed_roles: List[UserRole]):
    """
    Role-Based Access Control (RBAC) dependency factory.
    Enforces that the current authenticated user possesses one of the allowed roles.
    """
    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role")
        # Check against enum values or strings
        allowed_values = [r.value if isinstance(r, UserRole) else str(r) for r in allowed_roles]
        
        if user_role not in allowed_values:
            logger.warning(
                "Access forbidden: User %s with role '%s' attempted to access endpoint restricted to %s",
                current_user.get("email"),
                user_role,
                allowed_values
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: Insufficient permissions. Required role(s): {', '.join(allowed_values)}"
            )
        return current_user

    return role_checker


# Convenient role shortcuts
require_admin = require_roles([UserRole.ADMIN])
require_farmer_or_admin = require_roles([UserRole.FARMER, UserRole.ADMIN])

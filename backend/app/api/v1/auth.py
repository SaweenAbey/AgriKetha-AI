from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from bson import ObjectId
from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.config import settings
from app.core.middleware import record_audit_log
from app.core.logging_config import logger
from app.schemas.user import UserRegister, UserLogin, UserOut
from app.schemas.token import Token, RefreshTokenRequest
from app.models.user import UserRole
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserRegister, request: Request, db = Depends(get_db)):
    """
    Registers a new user (defaults to role: 'farmer').
    Checks for email uniqueness and stores hashed password in MongoDB.
    """
    client_ip = request.client.host if request.client else None
    email_clean = user_in.email.lower().strip()

    # Check if user already exists
    existing_user = await db.users.find_one({"email": email_clean})
    if existing_user:
        logger.warning("Registration failed: Email %s already registered", email_clean)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    hashed_pw = get_password_hash(user_in.password)
    now = datetime.now(timezone.utc)

    user_dict = {
        "email": email_clean,
        "hashed_password": hashed_pw,
        "full_name": user_in.full_name.strip(),
        "phone_number": user_in.phone_number.strip() if user_in.phone_number else None,
        "role": user_in.role.value if isinstance(user_in.role, UserRole) else str(user_in.role),
        "district": user_in.district.strip() if user_in.district else None,
        "is_active": True,
        "created_at": now,
        "updated_at": now
    }

    result = await db.users.insert_one(user_dict)
    user_id_str = str(result.inserted_id)
    user_dict["id"] = user_id_str

    # If farmer, auto-initialize basic farm record
    if user_dict["role"] == UserRole.FARMER.value:
        farm_dict = {
            "user_id": user_id_str,
            "farm_name": f"{user_in.full_name}'s Farm",
            "district": user_in.district or "Western",
            "area_or_village": None,
            "total_land_size_acres": 1.0,
            "soil_type": None,
            "irrigation_source": "Rainfed",
            "crops": [],
            "created_at": now,
            "updated_at": now
        }
        await db.farms.insert_one(farm_dict)

    await record_audit_log(
        action="USER_REGISTERED",
        user_id=user_id_str,
        user_email=email_clean,
        role=user_dict["role"],
        status="SUCCESS",
        details={"full_name": user_in.full_name, "district": user_in.district},
        ip_address=client_ip
    )

    logger.info("Successfully registered user: %s (Role: %s)", email_clean, user_dict["role"])
    return UserOut(**user_dict)


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, request: Request, db = Depends(get_db)):
    """
    Authenticates user credentials and returns JWT Access & Refresh tokens.
    """
    client_ip = request.client.host if request.client else None
    email_clean = credentials.email.lower().strip()

    user = await db.users.find_one({"email": email_clean})
    if not user or not verify_password(credentials.password, user.get("hashed_password", "")):
        logger.warning("Failed login attempt for email: %s from IP: %s", email_clean, client_ip)
        await record_audit_log(
            action="USER_LOGIN_FAILED",
            user_email=email_clean,
            status="FAILED",
            details={"reason": "Invalid email or password"},
            ip_address=client_ip
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.get("is_active", True):
        logger.warning("Deactivated user attempted login: %s", email_clean)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact an administrator."
        )

    user_id_str = str(user["_id"])
    role = user.get("role", UserRole.FARMER.value)

    access_token = create_access_token(subject=user_id_str, role=role)
    refresh_token = create_refresh_token(subject=user_id_str, role=role)

    user_out = UserOut(
        id=user_id_str,
        email=user["email"],
        full_name=user["full_name"],
        phone_number=user.get("phone_number"),
        role=user["role"],
        district=user.get("district"),
        is_active=user.get("is_active", True),
        created_at=user["created_at"],
        updated_at=user["updated_at"]
    )

    await record_audit_log(
        action="USER_LOGIN_SUCCESS",
        user_id=user_id_str,
        user_email=email_clean,
        role=role,
        status="SUCCESS",
        details={"method": "password"},
        ip_address=client_ip
    )

    logger.info("User logged in successfully: %s (Role: %s)", email_clean, role)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_out.model_dump()
    )


@router.get("/me", response_model=UserOut)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """
    Returns the current authenticated user profile.
    """
    return UserOut(**current_user)


@router.post("/refresh")
async def refresh_access_token(payload: RefreshTokenRequest, db = Depends(get_db)):
    """
    Issues a new access token given a valid refresh token.
    """
    token_data = decode_token(payload.refresh_token)
    if token_data is None or token_data.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = token_data.get("sub")
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user or not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer active or found."
        )

    new_access_token = create_access_token(subject=str(user["_id"]), role=user.get("role", "farmer"))
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

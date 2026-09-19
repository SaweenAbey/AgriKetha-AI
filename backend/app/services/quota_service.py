from datetime import datetime, timezone
from typing import Any, Optional, Tuple
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.logging_config import logger


# Daily Quotas for Normal / Free Tier users
FREE_DAILY_TEXT_LIMIT = 25
FREE_DAILY_IMAGE_LIMIT = 5
FREE_DAILY_VOICE_LIMIT = 5


class QuotaService:
    """
    Manages daily usage tracking and rate limits for AgriKetha-AI users.
    Normal/Free users:
      - 25 text queries per day
      - 5 image analyses per day
      - 5 voice analyses per day
    Subscription / Premium / Admin users:
      - Unlimited text, image, and voice analyses.
    """

    @staticmethod
    def get_current_date_str() -> str:
        """Returns the current UTC date string YYYY-MM-DD."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    @classmethod
    async def get_or_create_daily_usage(
        cls,
        db: AsyncIOMotorDatabase,
        user_id: str,
        date_str: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Retrieves or initializes today's quota document for the given user.
        """
        if not date_str:
            date_str = cls.get_current_date_str()

        usage_doc = await db.user_quotas.find_one({
            "user_id": str(user_id),
            "date": date_str
        })

        if not usage_doc:
            now = datetime.now(timezone.utc)
            new_doc = {
                "user_id": str(user_id),
                "date": date_str,
                "text_count": 0,
                "image_count": 0,
                "voice_count": 0,
                "created_at": now,
                "updated_at": now
            }
            await db.user_quotas.insert_one(new_doc)
            usage_doc = new_doc

        return usage_doc

    @classmethod
    async def get_user_quota_status(
        cls,
        db: AsyncIOMotorDatabase,
        user: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Calculates current daily usage, limits, and remaining allowance for user.
        """
        user_id = str(user.get("id") or user.get("_id"))
        role = user.get("role", "farmer")
        plan = user.get("plan", "free")
        is_premium = (plan in ["premium", "pro", "subscription"]) or (role == "admin")

        usage = await cls.get_or_create_daily_usage(db, user_id)
        text_used = usage.get("text_count", 0)
        image_used = usage.get("image_count", 0)
        voice_used = usage.get("voice_count", 0)

        if is_premium:
            return {
                "plan": "premium",
                "is_unlimited": True,
                "date": usage.get("date", cls.get_current_date_str()),
                "text": {
                    "used": text_used,
                    "limit": None,
                    "remaining": None,
                    "unlimited": True
                },
                "image": {
                    "used": image_used,
                    "limit": None,
                    "remaining": None,
                    "unlimited": True
                },
                "voice": {
                    "used": voice_used,
                    "limit": None,
                    "remaining": None,
                    "unlimited": True
                }
            }

        # Free tier calculations
        text_remaining = max(0, FREE_DAILY_TEXT_LIMIT - text_used)
        image_remaining = max(0, FREE_DAILY_IMAGE_LIMIT - image_used)
        voice_remaining = max(0, FREE_DAILY_VOICE_LIMIT - voice_used)

        return {
            "plan": "free",
            "is_unlimited": False,
            "date": usage.get("date", cls.get_current_date_str()),
            "text": {
                "used": text_used,
                "limit": FREE_DAILY_TEXT_LIMIT,
                "remaining": text_remaining,
                "unlimited": False
            },
            "image": {
                "used": image_used,
                "limit": FREE_DAILY_IMAGE_LIMIT,
                "remaining": image_remaining,
                "unlimited": False
            },
            "voice": {
                "used": voice_used,
                "limit": FREE_DAILY_VOICE_LIMIT,
                "remaining": voice_remaining,
                "unlimited": False
            }
        }

    @classmethod
    async def check_and_consume_quota(
        cls,
        db: AsyncIOMotorDatabase,
        user: dict[str, Any],
        text_delta: int = 0,
        image_delta: int = 0,
        voice_delta: int = 0
    ) -> dict[str, Any]:
        """
        Validates whether the user has sufficient remaining quota for this request.
        If sufficient, increments the counts atomically and returns updated status.
        If exceeded, raises HTTP 429 Too Many Requests.
        """
        user_id = str(user.get("id") or user.get("_id"))
        role = user.get("role", "farmer")
        plan = user.get("plan", "free")
        is_premium = (plan in ["premium", "pro", "subscription"]) or (role == "admin")

        date_str = cls.get_current_date_str()
        usage = await cls.get_or_create_daily_usage(db, user_id, date_str)

        text_used = usage.get("text_count", 0)
        image_used = usage.get("image_count", 0)
        voice_used = usage.get("voice_count", 0)

        if not is_premium:
            exceeded = []
            if text_delta > 0 and (text_used + text_delta) > FREE_DAILY_TEXT_LIMIT:
                exceeded.append(f"Daily text query limit reached ({FREE_DAILY_TEXT_LIMIT}/day).")
            if image_delta > 0 and (image_used + image_delta) > FREE_DAILY_IMAGE_LIMIT:
                exceeded.append(f"Daily image analysis limit reached ({FREE_DAILY_IMAGE_LIMIT}/day).")
            if voice_delta > 0 and (voice_used + voice_delta) > FREE_DAILY_VOICE_LIMIT:
                exceeded.append(f"Daily voice analysis limit reached ({FREE_DAILY_VOICE_LIMIT}/day).")

            if exceeded:
                error_msg = " ".join(exceeded) + " Upgrade to AgriKetha Pro for unlimited access or wait for daily reset at 00:00 UTC."
                logger.warning("Quota exceeded for user %s | %s", user.get("email"), error_msg)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "message": error_msg,
                        "plan": "free",
                        "text": {"used": text_used, "limit": FREE_DAILY_TEXT_LIMIT},
                        "image": {"used": image_used, "limit": FREE_DAILY_IMAGE_LIMIT},
                        "voice": {"used": voice_used, "limit": FREE_DAILY_VOICE_LIMIT},
                        "upgrade_available": True
                    }
                )

        # Atomic increment in MongoDB
        inc_fields = {}
        if text_delta > 0:
            inc_fields["text_count"] = text_delta
        if image_delta > 0:
            inc_fields["image_count"] = image_delta
        if voice_delta > 0:
            inc_fields["voice_count"] = voice_delta

        if inc_fields:
            await db.user_quotas.update_one(
                {"user_id": user_id, "date": date_str},
                {
                    "$inc": inc_fields,
                    "$set": {"updated_at": datetime.now(timezone.utc)}
                },
                upsert=True
            )

        # Return updated quota status
        return await cls.get_user_quota_status(db, user)

    @classmethod
    async def set_user_subscription(
        cls,
        db: AsyncIOMotorDatabase,
        user_id: str,
        plan: str = "premium"
    ) -> dict[str, Any]:
        """
        Updates the user's subscription plan ('free' or 'premium').
        """
        from bson import ObjectId
        status_val = "active" if plan == "premium" else "none"
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "plan": plan,
                    "subscription_status": status_val,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        updated_user = await db.users.find_one({"_id": ObjectId(user_id)})
        updated_user["id"] = str(updated_user["_id"])
        return await cls.get_user_quota_status(db, updated_user)

import asyncio
import sys
import os
from bson import ObjectId

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import connect_to_mongo, get_db
from app.services.quota_service import (
    QuotaService,
    FREE_DAILY_TEXT_LIMIT,
    FREE_DAILY_IMAGE_LIMIT,
    FREE_DAILY_VOICE_LIMIT,
)

async def run_quota_tests():
    print("=== Starting Quota & Subscription System Verification ===")
    await connect_to_mongo()
    db = get_db()

    # Find or test with a test user ID
    user = await db.users.find_one({"email": "farmer@agriketha.ai"})
    if not user:
        print("Creating mock user for testing...")
        test_user = {
            "email": "quota_test@agriketha.ai",
            "full_name": "Quota Test User",
            "role": "farmer",
            "plan": "free",
            "subscription_status": "none"
        }
        res = await db.users.insert_one(test_user)
        user = await db.users.find_one({"_id": res.inserted_id})

    user_id = str(user["_id"])
    user["id"] = user_id

    # Reset user to free plan for test
    await QuotaService.set_user_subscription(db, user_id, "free")
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    user["id"] = str(user["_id"])

    # Clean today's quota for user to have clean slate
    await db.user_quotas.delete_many({"user_id": user_id})

    # 1. Check initial quota
    status = await QuotaService.get_user_quota_status(db, user)
    print(f"[1] Initial Quota Status: Plan={status['plan']}, Text={status['text']['used']}/{status['text']['limit']}, Image={status['image']['used']}/{status['image']['limit']}, Voice={status['voice']['used']}/{status['voice']['limit']}, Unlimited={status['is_unlimited']}")
    assert status["plan"] == "free"
    assert status["text"]["limit"] == FREE_DAILY_TEXT_LIMIT
    assert status["image"]["limit"] == FREE_DAILY_IMAGE_LIMIT
    assert status["voice"]["limit"] == FREE_DAILY_VOICE_LIMIT
    assert status["text"]["used"] == 0
    assert status["is_unlimited"] is False

    # 2. Consume 1 text query
    res = await QuotaService.check_and_consume_quota(db, user, text_delta=1)
    assert res["text"]["used"] == 1
    assert res["text"]["remaining"] == 24
    print(f"[2] Consumed 1 text query: Remaining={res['text']['remaining']}")

    # 3. Consume 1 image and 1 voice query
    res = await QuotaService.check_and_consume_quota(db, user, image_delta=1, voice_delta=1)
    assert res["image"]["used"] == 1
    assert res["image"]["remaining"] == 4
    assert res["voice"]["used"] == 1
    assert res["voice"]["remaining"] == 4
    print(f"[3] Consumed image & voice: Image Remaining={res['image']['remaining']}, Voice Remaining={res['voice']['remaining']}")

    # 4. Upgrade to Pro/Premium Subscription
    upgrade_res = await QuotaService.set_user_subscription(db, user_id, "premium")
    print(f"[4] Upgraded to Premium: Plan={upgrade_res['plan']}, Unlimited={upgrade_res['is_unlimited']}")
    assert upgrade_res["plan"] == "premium"
    assert upgrade_res["is_unlimited"] is True

    # 5. Verify Pro user can execute queries with zero limits
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    user["id"] = str(user["_id"])
    res_unlimited = await QuotaService.check_and_consume_quota(db, user, voice_delta=10)
    print(f"[5] Pro Unlimited Query Check: Unlimited={res_unlimited['is_unlimited']}")
    assert res_unlimited["is_unlimited"] is True

    # 6. Reset user to free plan with fresh counters
    await QuotaService.set_user_subscription(db, user_id, "free")
    await db.user_quotas.delete_many({"user_id": user_id})
    print("=== All Quota & Subscription Tests Passed Successfully! ===")

if __name__ == "__main__":
    asyncio.run(run_quota_tests())

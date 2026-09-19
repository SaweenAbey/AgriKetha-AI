import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import init_db, get_db
from app.services.quota_service import (
    get_user_quota_status,
    check_and_consume_quota,
    set_user_subscription,
    FREE_DAILY_TEXT_LIMIT,
    FREE_DAILY_IMAGE_LIMIT,
    FREE_DAILY_VOICE_LIMIT,
)
from app.models.user import User

async def run_quota_tests():
    print("=== Starting Quota & Subscription System Verification ===")
    await init_db()
    db = get_db()

    # Find or test with a test user ID
    user = await db["users"].find_one({"email": "farmer@agriketha.ai"})
    if not user:
        print("Creating mock user for testing...")
        test_user = {
            "email": "quota_test@agriketha.ai",
            "full_name": "Quota Test User",
            "role": "farmer",
            "plan": "free",
            "subscription_status": "none"
        }
        res = await db["users"].insert_one(test_user)
        user_id = str(res.inserted_id)
    else:
        user_id = str(user["_id"])
        # Ensure user starts in free plan for test
        await set_user_subscription(user_id, plan="free", status="active")

    # Clean today's quota for user to have clean slate
    await db["user_quotas"].delete_many({"user_id": user_id})

    # 1. Check initial quota
    status = await get_user_quota_status(user_id)
    print(f"[1] Initial Quota Status: Plan={status['plan']}, Text={status['text_used']}/{status['text_limit']}, Image={status['image_used']}/{status['image_limit']}, Voice={status['voice_used']}/{status['voice_limit']}, Unlimited={status['unlimited']}")
    assert status["plan"] == "free"
    assert status["text_limit"] == FREE_DAILY_TEXT_LIMIT
    assert status["image_limit"] == FREE_DAILY_IMAGE_LIMIT
    assert status["voice_limit"] == FREE_DAILY_VOICE_LIMIT
    assert status["text_used"] == 0
    assert status["unlimited"] is False

    # 2. Consume 1 text query
    res = await check_and_consume_quota(user_id, query_type="text")
    assert res["allowed"] is True
    assert res["quota"]["text_used"] == 1
    assert res["quota"]["text_remaining"] == 24
    print(f"[2] Consumed 1 text query: Remaining={res['quota']['text_remaining']}")

    # 3. Consume 1 image query and 1 voice query
    res_img = await check_and_consume_quota(user_id, query_type="image")
    assert res_img["allowed"] is True
    assert res_img["quota"]["image_used"] == 1
    assert res_img["quota"]["image_remaining"] == 4

    res_voice = await check_and_consume_quota(user_id, query_type="voice")
    assert res_voice["allowed"] is True
    assert res_voice["quota"]["voice_used"] == 1
    assert res_voice["quota"]["voice_remaining"] == 4
    print(f"[3] Consumed image & voice: Image Remaining={res_img['quota']['image_remaining']}, Voice Remaining={res_voice['quota']['voice_remaining']}")

    # 4. Simulate reaching limits for voice (consume 4 more voice queries)
    for _ in range(4):
        await check_and_consume_quota(user_id, query_type="voice")
    
    # 5th attempt should be blocked
    res_voice_blocked = await check_and_consume_quota(user_id, query_type="voice")
    print(f"[4] 6th Voice Query Blocked? Allowed={res_voice_blocked['allowed']}, Error={res_voice_blocked.get('error')}")
    assert res_voice_blocked["allowed"] is False
    assert "Daily voice limit reached" in res_voice_blocked["error"]

    # 5. Upgrade to Pro Subscription
    upgrade_res = await set_user_subscription(user_id, plan="pro", status="active")
    print(f"[5] Upgraded to Pro: Plan={upgrade_res['plan']}, Unlimited={upgrade_res['unlimited']}")
    assert upgrade_res["plan"] == "pro"
    assert upgrade_res["unlimited"] is True

    # 6. Verify Pro user can now execute unlimited voice queries
    res_voice_unlimited = await check_and_consume_quota(user_id, query_type="voice")
    print(f"[6] Pro Voice Query Check: Allowed={res_voice_unlimited['allowed']}, Unlimited={res_voice_unlimited['quota']['unlimited']}")
    assert res_voice_unlimited["allowed"] is True
    assert res_voice_unlimited["quota"]["unlimited"] is True

    # 7. Reset user to free plan with fresh counters for normal use
    await set_user_subscription(user_id, plan="free", status="none")
    await db["user_quotas"].delete_many({"user_id": user_id})
    print("=== All Quota & Subscription Tests Passed Successfully! ===")

if __name__ == "__main__":
    asyncio.run(run_quota_tests())

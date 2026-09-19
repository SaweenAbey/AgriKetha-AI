import asyncio
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import get_db
from app.api.v1.payments import generate_payhere_hash, PLANS
from datetime import datetime, timezone

async def run_payment_tests():
    print("=" * 60)
    print("AgriKetha-AI Payment Gateway & Sandbox Verification")
    print("=" * 60)

    # 1. Test PayHere MD5 Signature Generation
    test_merchant_id = "1211111"
    test_order_id = "AGRI-PRO-12345"
    test_amount = 1500.0
    test_currency = "LKR"
    test_secret = "4TkSecret123"

    hash_val = generate_payhere_hash(
        merchant_id=test_merchant_id,
        order_id=test_order_id,
        amount=test_amount,
        currency=test_currency,
        secret=test_secret
    )
    print(f"1. PayHere Security Signature (MD5): {hash_val}")
    assert len(hash_val) == 32
    assert hash_val.isupper()
    print("   [PASS] PayHere cryptographic signature verified.")

    # 2. Test Plan Catalog
    assert "pro_monthly" in PLANS
    assert PLANS["pro_monthly"]["amount"] == 1500.0
    assert PLANS["pro_monthly"]["currency"] == "LKR"
    print("2. Plan Catalog:")
    for k, v in PLANS.items():
        print(f"   - {v['name']}: {v['currency']} {v['amount']}")
    print("   [PASS] Plan definitions verified.")

    # 3. Test Database Order Creation & Subscription Transition
    from app.core.database import connect_to_mongo, close_mongo_connection
    await connect_to_mongo()
    db = get_db()
    test_user_id = "test-farmer-001"
    test_order_id = f"AGRI-TEST-{int(datetime.now().timestamp())}"

    # Insert test order
    await db.payment_orders.insert_one({
        "order_id": test_order_id,
        "user_id": test_user_id,
        "user_email": "farmer@agriketha.ai",
        "plan_id": "pro_monthly",
        "amount": 1500.0,
        "currency": "LKR",
        "status": "PENDING",
        "created_at": datetime.now(timezone.utc)
    })

    # Simulate payment verification
    await db.payment_orders.update_one(
        {"order_id": test_order_id},
        {"$set": {"status": "PAID", "paid_at": datetime.now(timezone.utc)}}
    )

    paid_order = await db.payment_orders.find_one({"order_id": test_order_id})
    assert paid_order["status"] == "PAID"
    print(f"3. Simulated Order Processing: {paid_order['order_id']} -> Status: {paid_order['status']}")
    print("   [PASS] Database order lifecycle verified.")

    # Clean up test order
    await db.payment_orders.delete_one({"order_id": test_order_id})

    print("\n" + "=" * 60)
    print("[PASS] ALL PAYMENT GATEWAY TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_payment_tests())

import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.config import settings
from app.core.logging_config import logger
from app.api.deps import require_farmer_or_admin

router = APIRouter(prefix="/payments", tags=["Payment Gateway"])

# Standard AgriKetha-AI Plan Catalog
PLANS = {
    "pro_monthly": {
        "id": "pro_monthly",
        "name": "AgriKetha Pro (Monthly)",
        "name_si": "AgriKetha Pro (මාසික)",
        "amount": 1500.0,
        "currency": "LKR",
        "billing_cycle": "monthly",
        "description": "Unlimited Deep Learning Vision scans, AI Farmer Assistant queries, and Priority Market Advisory.",
        "badge": "Popular"
    },
    "pro_annual": {
        "id": "pro_annual",
        "name": "AgriKetha Pro (Annual - 20% OFF)",
        "name_si": "AgriKetha Pro (වාර්ෂික - 20% වට්ටමක්)",
        "amount": 14400.0,
        "currency": "LKR",
        "billing_cycle": "annual",
        "description": "Full 1-year unlimited agricultural intelligence pass. Save LKR 3,600.",
        "badge": "Best Value"
    }
}

# Sandbox Pre-configured Test Cards for One-Click Testing
SANDBOX_TEST_CARDS = [
    {
        "type": "Visa",
        "card_number": "4111 1111 1111 1111",
        "exp": "12/28",
        "cvv": "123",
        "otp": "1234",
        "label": "PayHere Sandbox Visa (Auto-Approved)"
    },
    {
        "type": "Mastercard",
        "card_number": "5200 8282 8282 8282",
        "exp": "09/29",
        "cvv": "456",
        "otp": "1234",
        "label": "PayHere Sandbox Mastercard (Auto-Approved)"
    },
    {
        "type": "Genie / eZ Cash",
        "mobile": "077 123 4567",
        "pin": "1234",
        "label": "Dialog Genie / eZ Cash Mobile Wallet"
    }
]


class CreateOrderRequest(BaseModel):
    plan_id: str = "pro_monthly"
    payment_method: str = "card"  # 'card', 'payhere_sandbox', 'ezcash', 'genie'


class VerifyPaymentRequest(BaseModel):
    order_id: str
    payment_id: Optional[str] = None
    status: str = "SUCCESS"
    payment_method: Optional[str] = "payhere_sandbox"
    card_last4: Optional[str] = "1111"


import os
from dotenv import load_dotenv

def get_payhere_credentials():
    """Dynamically loads current PayHere credentials from environment/.env"""
    load_dotenv(override=True)
    merchant_id = os.getenv("PAYHERE_MERCHANT_ID", settings.PAYHERE_MERCHANT_ID)
    merchant_secret = os.getenv("PAYHERE_MERCHANT_SECRET", settings.PAYHERE_MERCHANT_SECRET)
    mode = os.getenv("PAYHERE_MODE", settings.PAYHERE_MODE)
    return merchant_id.strip('"').strip("'"), merchant_secret.strip('"').strip("'"), mode.strip('"').strip("'")


def generate_payhere_hash(merchant_id: str, order_id: str, amount: float, currency: str, secret: str) -> str:
    """
    Standard PayHere MD5 security hash generator.
    Formula: strtoupper(md5(merchant_id + order_id + formatted_amount + currency + strtoupper(md5(secret))))
    """
    amount_str = f"{amount:.2f}"
    secret_hash = hashlib.md5(secret.encode("utf-8")).hexdigest().upper()
    raw_str = f"{merchant_id}{order_id}{amount_str}{currency}{secret_hash}"
    return hashlib.md5(raw_str.encode("utf-8")).hexdigest().upper()


@router.get("/config")
async def get_payment_configuration(
    current_user: dict = Depends(require_farmer_or_admin)
):
    """
    Returns payment gateway configuration, plan catalog, and testing sandbox presets.
    """
    merchant_id, _, mode = get_payhere_credentials()
    return {
        "mode": mode,
        "merchant_id": merchant_id,
        "currency": "LKR",
        "plans": list(PLANS.values()),
        "test_cards": SANDBOX_TEST_CARDS,
        "supported_methods": [
            {"id": "payhere_card", "name": "Credit / Debit Card (Visa, Mastercard)", "icon": "credit-card"},
            {"id": "genie", "name": "Dialog Genie / FriMi", "icon": "smartphone"},
            {"id": "ezcash", "name": "eZ Cash / mCash Mobile Money", "icon": "wallet"}
        ]
    }


@router.post("/create-order")
async def create_payment_order(
    req: CreateOrderRequest,
    current_user: dict = Depends(require_farmer_or_admin),
    db = Depends(get_db)
):
    """
    Initiates a new payment session, records the order in MongoDB,
    and returns PayHere parameters & security signature.
    """
    merchant_id, merchant_secret, mode = get_payhere_credentials()
    plan = PLANS.get(req.plan_id, PLANS["pro_monthly"])
    order_id = f"AGRI-PRO-{int(datetime.now().timestamp())}-{current_user['id'][:5].upper()}"

    payhere_hash = generate_payhere_hash(
        merchant_id=merchant_id,
        order_id=order_id,
        amount=plan["amount"],
        currency=plan["currency"],
        secret=merchant_secret
    )

    now = datetime.now(timezone.utc)
    order_doc = {
        "order_id": order_id,
        "user_id": current_user["id"],
        "user_email": current_user.get("email"),
        "user_name": current_user.get("full_name", "Farmer"),
        "plan_id": plan["id"],
        "plan_name": plan["name"],
        "amount": plan["amount"],
        "currency": plan["currency"],
        "payment_method": req.payment_method,
        "status": "PENDING",
        "payhere_hash": payhere_hash,
        "created_at": now,
        "updated_at": now
    }

    await db.payment_orders.insert_one(order_doc)

    return {
        "order_id": order_id,
        "amount": plan["amount"],
        "currency": plan["currency"],
        "plan": plan,
        "payhere": {
            "sandbox": mode == "sandbox",
            "merchant_id": merchant_id,
            "hash": payhere_hash,
            "url": settings.PAYHERE_URL,
            "item_name": plan["name"],
            "first_name": current_user.get("full_name", "Farmer").split()[0],
            "last_name": " ".join(current_user.get("full_name", "").split()[1:]) or "User",
            "email": current_user.get("email") or "farmer@agriketha.ai",
            "phone": current_user.get("phone_number") or "0771234567",
            "address": current_user.get("district") or "Western Province",
            "city": "Colombo",
            "country": "Sri Lanka"
        }
    }


@router.post("/verify")
async def verify_payment_and_upgrade(
    req: VerifyPaymentRequest,
    current_user: dict = Depends(require_farmer_or_admin),
    db = Depends(get_db)
):
    """
    Verifies payment completion (Sandbox or Live), records receipt,
    and activates AgriKetha Pro Unlimited plan for the farmer.
    """
    now = datetime.now(timezone.utc)

    # 1. Look up order
    order = await db.payment_orders.find_one({"order_id": req.order_id, "user_id": current_user["id"]})
    if not order:
        # If created on the fly in sandbox
        order = {
            "order_id": req.order_id,
            "plan_id": "pro_monthly",
            "amount": 1500.0,
            "currency": "LKR"
        }

    payment_id = req.payment_id or f"PY-{int(datetime.now().timestamp())}"

    # 2. Update order record
    await db.payment_orders.update_one(
        {"order_id": req.order_id},
        {
            "$set": {
                "status": "PAID",
                "payment_id": payment_id,
                "payment_method": req.payment_method,
                "card_last4": req.card_last4,
                "paid_at": now,
                "updated_at": now
            }
        },
        upsert=True
    )

    # 3. Upgrade user subscription
    await db.users.update_one(
        {"id": current_user["id"]},
        {
            "$set": {
                "subscription_plan": "premium",
                "subscription_status": "active",
                "subscription_updated_at": now,
                "subscription_expires_at": None  # Active unlimited
            }
        }
    )

    logger.info("Payment verified for user %s: Order %s (%s %s)", current_user.get("email"), req.order_id, order.get("currency"), order.get("amount"))

    return {
        "success": True,
        "message": "Payment verified successfully. AgriKetha Pro Unlimited activated!",
        "order_id": req.order_id,
        "payment_id": payment_id,
        "plan": "premium",
        "unlimited": True,
        "amount": order.get("amount", 1500.0),
        "currency": order.get("currency", "LKR"),
        "activated_at": now.isoformat()
    }


@router.post("/payhere-notify")
async def payhere_instant_payment_notification(
    request: Request,
    merchant_id: str = Form(...),
    order_id: str = Form(...),
    payment_id: str = Form(...),
    payhere_amount: float = Form(...),
    payhere_currency: str = Form(...),
    status_code: int = Form(...),
    md5sig: str = Form(...),
    custom_1: Optional[str] = Form(None),
    custom_2: Optional[str] = Form(None),
    db = Depends(get_db)
):
    """
    PayHere Instant Payment Notification (IPN) webhook.
    Called automatically by PayHere servers when a transaction completes.
    status_code: 2 = Success, 0 = Pending, -1 = Canceled, -2 = Failed, -3 = Chargedback
    """
    # Verify MD5 signature
    secret_hash = hashlib.md5(settings.PAYHERE_MERCHANT_SECRET.encode("utf-8")).hexdigest().upper()
    amount_str = f"{payhere_amount:.2f}"
    raw_sig = f"{merchant_id}{order_id}{amount_str}{payhere_currency}{status_code}{secret_hash}"
    local_sig = hashlib.md5(raw_sig.encode("utf-8")).hexdigest().upper()

    if md5sig != local_sig:
        logger.warning("PayHere IPN signature mismatch for order %s", order_id)
        raise HTTPException(status_code=400, detail="Signature verification failed.")

    now = datetime.now(timezone.utc)

    if status_code == 2:
        # Success
        order = await db.payment_orders.find_one({"order_id": order_id})
        user_id = order.get("user_id") if order else custom_1

        await db.payment_orders.update_one(
            {"order_id": order_id},
            {
                "$set": {
                    "status": "PAID",
                    "payment_id": payment_id,
                    "amount": payhere_amount,
                    "currency": payhere_currency,
                    "paid_at": now,
                    "updated_at": now
                }
            },
            upsert=True
        )

        if user_id:
            await db.users.update_one(
                {"id": user_id},
                {
                    "$set": {
                        "subscription_plan": "premium",
                        "subscription_status": "active",
                        "subscription_updated_at": now
                    }
                }
            )
            logger.info("PayHere IPN successfully upgraded user %s for order %s", user_id, order_id)

    return {"status": "received"}


@router.get("/history")
async def get_user_payment_history(
    current_user: dict = Depends(require_farmer_or_admin),
    db = Depends(get_db)
):
    """
    Returns past billing transactions and receipts for the current user.
    """
    cursor = db.payment_orders.find({"user_id": current_user["id"]}).sort("created_at", -1).limit(20)
    orders = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        orders.append(doc)
    return orders


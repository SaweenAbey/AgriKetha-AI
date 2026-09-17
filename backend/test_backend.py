import asyncio
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection, db_state
from app.core.security import create_access_token, verify_password, get_password_hash
from app.models.user import UserRole
import httpx


async def run_tests():
    print("=" * 60)
    print(" AgriKetha-AI Backend Automated Verification Suite")
    print("=" * 60)

    # 1. MongoDB Connection Test
    print("\n[1] Testing MongoDB Connection & Atlas Connectivity...")
    try:
        await connect_to_mongo()
        db = db_state.db
        assert db is not None
        ping_res = await db.client.admin.command('ping')
        print("  -> MongoDB Ping Response:", ping_res)
        print("  -> [PASS] Database connection verified.")
    except Exception as e:
        print("  -> [FAIL] MongoDB Connection Error:", e)
        return

    # 2. Security & Hashing Test
    print("\n[2] Testing Password Hashing & JWT Token Generation...")
    raw_pass = "SecurePass123!"
    hashed = get_password_hash(raw_pass)
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPass", hashed) is False
    token = create_access_token(subject="user_123", role="farmer")
    print("  -> [PASS] Password hashing & JWT generation verified.")

    # 3. Clean up and run FastAPI app test with httpx
    print("\n[3] Testing API Endpoints via ASGI Test Client...")
    from app.main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 3.1 Health Check
        health_resp = await client.get("/health")
        print(f"  -> GET /health: {health_resp.status_code} | {health_resp.json()}")
        assert health_resp.status_code == 200

        # 3.2 Register Farmer
        farmer_data = {
            "email": "test_farmer_auto@agriketha.ai",
            "password": "FarmerPassword123!",
            "full_name": "Test Farmer Automated",
            "phone_number": "+94770001122",
            "role": "farmer",
            "district": "Kurunegala"
        }
        # Clean existing test user if any
        await db.users.delete_many({"email": {"$in": ["test_farmer_auto@agriketha.ai", "test_admin_auto@agriketha.ai"]}})
        await db.farms.delete_many({"district": "Kurunegala", "farm_name": "Test Farmer Automated's Farm"})

        reg_resp = await client.post("/api/v1/auth/register", json=farmer_data)
        print(f"  -> POST /api/v1/auth/register (Farmer): {reg_resp.status_code}")
        assert reg_resp.status_code == 201

        # 3.3 Login Farmer
        login_resp = await client.post("/api/v1/auth/login", json={
            "email": "test_farmer_auto@agriketha.ai",
            "password": "FarmerPassword123!"
        })
        print(f"  -> POST /api/v1/auth/login (Farmer): {login_resp.status_code}")
        assert login_resp.status_code == 200
        farmer_token = login_resp.json()["access_token"]

        # 3.4 Get /me
        me_resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {farmer_token}"})
        print(f"  -> GET /api/v1/auth/me: {me_resp.status_code} | Role: {me_resp.json().get('role')}")
        assert me_resp.status_code == 200
        assert me_resp.json()["role"] == "farmer"

        # 3.5 Farmer access Farmer Profile (Allowed)
        farmer_prof = await client.get("/api/v1/farmer/profile", headers={"Authorization": f"Bearer {farmer_token}"})
        print(f"  -> GET /api/v1/farmer/profile: {farmer_prof.status_code} | Farm: {farmer_prof.json().get('farm_name')}")
        assert farmer_prof.status_code == 200

        # 3.6 Farmer add Crop
        crop_resp = await client.post("/api/v1/farmer/crops", json={
            "name": "Maize",
            "variety": "Pacific 999",
            "acres_planted": 2.0,
            "stage": "vegetative"
        }, headers={"Authorization": f"Bearer {farmer_token}"})
        print(f"  -> POST /api/v1/farmer/crops: {crop_resp.status_code} | Crops count: {len(crop_resp.json())}")
        assert crop_resp.status_code == 200

        # 3.7 Farmer sends Query to Agent 1 (Text & Voice modes)
        query_text_resp = await client.post("/api/v1/farmer/query-agent", json={
            "question": "My tomato leaves are turning yellow with brown spots.",
            "input_mode": "text",
            "auto_triggered": False
        }, headers={"Authorization": f"Bearer {farmer_token}"})
        print(f"  -> POST /api/v1/farmer/query-agent (Text Mode): {query_text_resp.status_code} | Crop: {query_text_resp.json()['agent_response']['agent_1_result']['crop']}")
        assert query_text_resp.status_code == 200
        assert query_text_resp.json()["agent_response"]["agent_1_result"]["crop"] == "tomato"
        assert "yellow leaves" in query_text_resp.json()["agent_response"]["agent_1_result"]["symptoms"]

        # Voice mode auto-triggered query test
        query_voice_resp = await client.post("/api/v1/farmer/query-agent", json={
            "question": "What is the best fertilizer dosage for paddy during vegetative growth?",
            "input_mode": "voice",
            "auto_triggered": True
        }, headers={"Authorization": f"Bearer {farmer_token}"})
        print(f"  -> POST /api/v1/farmer/query-agent (Voice Mode): {query_voice_resp.status_code} | Intent: {query_voice_resp.json()['agent_response']['agent_1_result']['intent']}")
        assert query_voice_resp.status_code == 200
        assert query_voice_resp.json()["agent_response"]["agent_1_result"]["crop"] == "rice"

        # Sinhala Query test
        query_sinhala_resp = await client.post("/api/v1/farmer/query-agent", json={
            "question": "මගේ තක්කාලි වල කළුපාට ලප තියෙනවා",
            "input_mode": "voice",
            "auto_triggered": True
        }, headers={"Authorization": f"Bearer {farmer_token}"})
        print(f"  -> POST /api/v1/farmer/query-agent (Sinhala Query): {query_sinhala_resp.status_code} | Crop: {query_sinhala_resp.json()['agent_response']['agent_1_result']['crop']} | Symptoms: {query_sinhala_resp.json()['agent_response']['agent_1_result']['symptoms']}")
        assert query_sinhala_resp.status_code == 200
        assert query_sinhala_resp.json()["agent_response"]["agent_1_result"]["crop"] == "tomato"
        assert "brown spots" in query_sinhala_resp.json()["agent_response"]["agent_1_result"]["symptoms"]
        assert query_sinhala_resp.json()["agent_response"]["agent_1_result"]["intent"] == "disease diagnosis"

        # Farmer checks Agent 1 status
        status_resp = await client.get("/api/v1/farmer/agent-1-status")
        print(f"  -> GET /api/v1/farmer/agent-1-status: {status_resp.status_code} | Status: {status_resp.json().get('status')}")
        assert status_resp.status_code == 200


        # 3.8 RBAC Security Test: Farmer attempts to access Admin endpoint (Must receive 403 Forbidden)
        forbidden_resp = await client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {farmer_token}"})
        print(f"  -> [RBAC CHECK] GET /api/v1/admin/users with Farmer token: {forbidden_resp.status_code} (Expected 403)")
        assert forbidden_resp.status_code == 403


        # 3.8 Register & Login Admin
        admin_data = {
            "email": "test_admin_auto@agriketha.ai",
            "password": "AdminPassword123!",
            "full_name": "Test Admin Automated",
            "role": "admin",
            "district": "Colombo"
        }
        await client.post("/api/v1/auth/register", json=admin_data)
        admin_login = await client.post("/api/v1/auth/login", json={
            "email": "test_admin_auto@agriketha.ai",
            "password": "AdminPassword123!"
        })
        admin_token = admin_login.json()["access_token"]

        # 3.9 Admin accesses Admin endpoints (Allowed)
        admin_users_resp = await client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
        print(f"  -> [RBAC CHECK] GET /api/v1/admin/users with Admin token: {admin_users_resp.status_code} | Users found: {len(admin_users_resp.json())}")
        assert admin_users_resp.status_code == 200

        admin_stats_resp = await client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
        print(f"  -> GET /api/v1/admin/stats: {admin_stats_resp.status_code} | Stats: {admin_stats_resp.json()}")
        assert admin_stats_resp.status_code == 200

        admin_audit_resp = await client.get("/api/v1/admin/audit-logs", headers={"Authorization": f"Bearer {admin_token}"})
        print(f"  -> GET /api/v1/admin/audit-logs: {admin_audit_resp.status_code} | Events: {len(admin_audit_resp.json())}")
        assert admin_audit_resp.status_code == 200

    await close_mongo_connection()
    print("\n" + "=" * 60)
    print(" ALL BACKEND VERIFICATION TESTS PASSED SUCCESSFULLY! ")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_tests())

import asyncio
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from datetime import datetime, timezone
from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection, db_state
from app.core.security import get_password_hash
from app.models.user import UserRole
from app.core.logging_config import logger, setup_logging


async def seed_initial_data():
    """
    Seeds initial admin and sample farmer users into MongoDB.
    """
    setup_logging()
    logger.info("Connecting to database for seeding...")
    await connect_to_mongo()

    db = db_state.db
    if db is None:
        logger.error("Database connection failed.")
        return

    now = datetime.now(timezone.utc)

    # 1. Seed Super Admin
    admin_email = "admin@agriketha.ai"
    existing_admin = await db.users.find_one({"email": admin_email})
    if not existing_admin:
        admin_doc = {
            "email": admin_email,
            "hashed_password": get_password_hash("Admin@123456"),
            "full_name": "AgriKetha Super Admin",
            "phone_number": "+94771234567",
            "role": UserRole.ADMIN.value,
            "district": "Colombo",
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }
        res = await db.users.insert_one(admin_doc)
        logger.info("Admin created: %s (Password: Admin@123456, ID: %s)", admin_email, res.inserted_id)
    else:
        logger.info("Admin user (%s) already exists.", admin_email)

    # 2. Seed Sample Farmer
    farmer_email = "farmer@agriketha.ai"
    existing_farmer = await db.users.find_one({"email": farmer_email})
    if not existing_farmer:
        farmer_doc = {
            "email": farmer_email,
            "hashed_password": get_password_hash("Farmer@123456"),
            "full_name": "Kamal Perera",
            "phone_number": "+94719876543",
            "role": UserRole.FARMER.value,
            "district": "Anuradhapura",
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }
        res = await db.users.insert_one(farmer_doc)
        farmer_id = str(res.inserted_id)
        logger.info("Farmer created: %s (Password: Farmer@123456, ID: %s)", farmer_email, farmer_id)

        # Create Farm profile for the farmer
        farm_doc = {
            "user_id": farmer_id,
            "farm_name": "Kamal Green Agro Farm",
            "district": "Anuradhapura",
            "area_or_village": "Thambuttegama",
            "total_land_size_acres": 2.5,
            "soil_type": "Reddish Brown Earths",
            "irrigation_source": "Major Tank / Canal",
            "crops": [
                {
                    "name": "Paddy (Rice)",
                    "variety": "Bg 352",
                    "planted_date": "2026-05-10",
                    "acres_planted": 1.5,
                    "stage": "vegetative"
                },
                {
                    "name": "Chilli",
                    "variety": "MICH 01",
                    "planted_date": "2026-06-01",
                    "acres_planted": 1.0,
                    "stage": "flowering"
                }
            ],
            "created_at": now,
            "updated_at": now
        }
        await db.farms.insert_one(farm_doc)
        logger.info("Sample Farm created for farmer %s", farmer_email)
    else:
        logger.info("Farmer user (%s) already exists.", farmer_email)

    await close_mongo_connection()
    logger.info("Seeding completed successfully.")


if __name__ == "__main__":
    asyncio.run(seed_initial_data())

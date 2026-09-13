from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import certifi
import dns.resolver
from app.core.config import settings
from app.core.logging_config import logger

# Ensure SRV DNS resolution works reliably across all Windows/network environments
try:
    dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
    dns.resolver.default_resolver.nameservers = ['8.8.8.8', '1.1.1.1', '8.8.4.4']
except Exception as _e:
    pass


class Database:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None


db_state = Database()


async def connect_to_mongo():
    """Establishes asynchronous connection to MongoDB Atlas."""
    logger.info("Connecting to MongoDB Atlas at: %s", settings.MONGODB_URL.split("@")[-1])
    try:
        db_state.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            tlsCAFile=certifi.where(),
            maxPoolSize=20,
            minPoolSize=1,
            maxIdleTimeMS=45000,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            socketTimeoutMS=20000,
            retryWrites=True,
            retryReads=True
        )
        db_state.db = db_state.client[settings.DATABASE_NAME]

        # Verify connection
        await db_state.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB Database: '%s'", settings.DATABASE_NAME)

        # Initialize collections and indexes
        await init_db_indexes()
    except Exception as e:
        logger.error("Failed to connect to MongoDB: %s", e, exc_info=True)
        raise e


async def close_mongo_connection():
    """Closes MongoDB connection pool."""
    if db_state.client:
        logger.info("Closing MongoDB connection pool...")
        db_state.client.close()
        logger.info("MongoDB connection pool closed.")


async def init_db_indexes():
    """Initializes indexes for MongoDB collections to enforce uniqueness and optimize queries."""
    if db_state.db is None:
        return

    try:
        # Users Collection Indexes
        await db_state.db.users.create_index("email", unique=True)
        await db_state.db.users.create_index("role")
        await db_state.db.users.create_index("is_active")
        await db_state.db.users.create_index("created_at")

        # Farms Collection Indexes
        await db_state.db.farms.create_index("user_id", unique=True)
        await db_state.db.farms.create_index("district")

        # Audit Logs Collection Indexes
        await db_state.db.audit_logs.create_index("created_at")
        await db_state.db.audit_logs.create_index("user_id")
        await db_state.db.audit_logs.create_index("action")

        # Farmer Queries Collection Indexes
        await db_state.db.farmer_queries.create_index("user_id")
        await db_state.db.farmer_queries.create_index("created_at")

        logger.info("MongoDB indexes verified & created successfully.")
    except Exception as e:
        logger.warning("Error creating MongoDB indexes: %s", e)


def get_db() -> AsyncIOMotorDatabase:
    """Dependency injection helper for database instance."""
    if db_state.db is None:
        raise RuntimeError("Database is not initialized. Ensure connect_to_mongo() was called.")
    return db_state.db

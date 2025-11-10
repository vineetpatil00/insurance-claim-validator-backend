from motor.motor_asyncio import AsyncIOMotorClient
from motor.core import AgnosticDatabase
from dotenv import load_dotenv
import certifi
import os
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    _database: AgnosticDatabase = None

    @classmethod
    async def connect(cls, uri: str, db_name: str = None):
        """Connect to MongoDB using Motor async driver."""
        try:
            # Attempt secure connection using certifi CA bundle
            cls.client = AsyncIOMotorClient(
                uri,
                tlsCAFile=certifi.where(),                # use trusted CA
                serverSelectionTimeoutMS=30000            # 30s timeout
            )
            # Fallback database name
            db_name = db_name or os.getenv("DB_NAME", "janshakti_digital")
            cls._database = cls.client[db_name]

            # Validate connection
            await cls.client.admin.command("ping")
            logger.info(f"✅ Connected to MongoDB database: {db_name}")

        except Exception as e:
            logger.error(f"⚠️ MongoDB connection failed: {e}")
            # Optional fallback for local dev if SSL cert fails
            try:
                cls.client = AsyncIOMotorClient(uri, tlsAllowInvalidCertificates=True)
                db_name = db_name or os.getenv("DB_NAME", "janshakti_digital")
                cls._database = cls.client[db_name]
                await cls.client.admin.command("ping")
                logger.warning("Connected using tlsAllowInvalidCertificates=True (dev mode)")
            except Exception as inner_e:
                logger.critical(f"❌ MongoDB connection failed completely: {inner_e}")
                cls.client = None
                cls._database = None

    @classmethod
    def get_database(cls, db_name: str = None) -> AgnosticDatabase:
        """Return database instance."""
        if db_name:
            return cls.client[db_name]
        if cls._database:
            return cls._database
        db_name = os.getenv("DB_NAME", "janshakti_digital")
        return cls.client[db_name]

    @classmethod
    async def connection_status(cls):
        """Check MongoDB connection status."""
        try:
            await cls.client.admin.command("ping")
            return {"status": "connected", "db": os.getenv("DB_NAME", "janshakti_digital")}
        except Exception as e:
            return {
                "status": "disconnected",
                "db": os.getenv("DB_NAME", "janshakti_digital"),
                "error": str(e)
            }

    @classmethod
    async def disconnect(cls):
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
            cls.client = None
            cls._database = None
            logger.info("🔌 MongoDB connection closed.")
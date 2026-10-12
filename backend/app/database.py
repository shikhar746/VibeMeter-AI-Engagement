"""
MongoDB connection manager for VibeMeter.
Encapsulates connection lifecycle and exposes typed collection handles.
"""

import certifi
import logging
import os

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase
from app.config import MONGODB_URI, MONGODB_DB

logger = logging.getLogger(__name__)

client: AsyncIOMotorClient | None = None
db: AsyncIOMotorDatabase | None = None
employees: AsyncIOMotorCollection | None = None
conversations: AsyncIOMotorCollection | None = None


async def connect_db() -> None:
    """Establish the MongoDB connection and initialise collection handles."""
    global client, db, employees, conversations
    uri = os.getenv("MONGODB_URI", MONGODB_URI)

    client = AsyncIOMotorClient(
        uri,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=10_000,
    )
    db = client[MONGODB_DB]
    employees = db["employees"]
    conversations = db["conversations"]

    try:
        await client.admin.command("ping")
        target_host = uri.split("@")[-1] if "@" in uri else uri
        print("\n==================================================")
        print(f"✅ SUCCESS: Connected to MongoDB ({target_host})")
        print("==================================================\n")
        logger.info("Connected to MongoDB at %s", target_host)
    except Exception as exc:
        logger.error(
            "MongoDB connection failed — verify your MONGODB_URI, network, "
            "and Atlas IP whitelist. Error: %s", exc
        )
        raise


async def close_db() -> None:
    """Gracefully close the MongoDB connection."""
    if client:
        client.close()
        logger.info("MongoDB connection closed")

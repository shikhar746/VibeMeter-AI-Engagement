from motor.motor_asyncio import AsyncIOMotorClient
import os

client = None
db = None
employees = None
conversations = None

async def connect_db():
    global client, db, employees, conversations
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(uri)
    db = client["vibemeter"]
    employees = db["employees"]
    conversations = db["conversations"]
    await client.admin.command("ping")
    print("✅ Connected to MongoDB")

async def close_db():
    if client:
        client.close()
        print("🔴 MongoDB connection closed")
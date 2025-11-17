import os
from datetime import datetime
from typing import Any, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorClient

DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "appdb")

_client: Optional[AsyncIOMotorClient] = None
_db = None

async def get_db():
    global _client, _db
    if _client is None:
        _client = AsyncIOMotorClient(DATABASE_URL)
        _db = _client[DATABASE_NAME]
    return _db

async def create_document(collection_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    db = await get_db()
    now = datetime.utcnow()
    doc = {**data, "created_at": now, "updated_at": now}
    res = await db[collection_name].insert_one(doc)
    doc["_id"] = str(res.inserted_id)
    # Convert datetime to isoformat for JSON serialisation
    doc["created_at"] = doc["created_at"].isoformat()
    doc["updated_at"] = doc["updated_at"].isoformat()
    return doc

async def get_documents(collection_name: str, filter_dict: Dict[str, Any] | None = None, limit: int = 50):
    db = await get_db()
    cursor = db[collection_name].find(filter_dict or {}).limit(limit).sort("created_at", -1)
    items = []
    async for item in cursor:
        item["_id"] = str(item["_id"])
        if isinstance(item.get("created_at"), datetime):
            item["created_at"] = item["created_at"].isoformat()
        if isinstance(item.get("updated_at"), datetime):
            item["updated_at"] = item["updated_at"].isoformat()
        items.append(item)
    return items

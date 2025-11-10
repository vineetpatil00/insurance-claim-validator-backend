from typing import List, Optional
from app.helpers.Database import MongoDB
from bson import ObjectId
import os
from datetime import datetime
from app.schemas.PyObjectId import PyObjectId
from dotenv import load_dotenv

load_dotenv()

class ClaimModel:
    def __init__(self, db_name=os.getenv('DB_NAME'), collection_name="Claims"):
        self.db_name = db_name
        self.collection_name = collection_name

    async def _get_collection(self):
        """Get the collection instance."""
        db = MongoDB.get_database(self.db_name)
        return db[self.collection_name]

    async def create_claim(self, data: dict) -> PyObjectId:
        """Create a new claim document."""
        data["CreatedOn"] = datetime.utcnow()
        data["IsDeleted"] = False
        collection = await self._get_collection()
        result = await collection.insert_one(data)
        return result.inserted_id

    async def get_claim(self, claim_id: str) -> Optional[dict]:
        """Retrieve a claim by ID."""
        collection = await self._get_collection()
        document = await collection.find_one(
            {"_id": ObjectId(claim_id), "IsDeleted": False}
        )
        return document

    async def update_claim(self, claim_id: str, updates: dict) -> bool:
        """Update an existing claim."""
        updates["UpdatedOn"] = datetime.utcnow()
        filters = {"_id": ObjectId(claim_id), "IsDeleted": False}
        collection = await self._get_collection()
        result = await collection.update_one(filters, {"$set": updates})
        return result.modified_count > 0

    async def push_to_array(self, claim_id: str, array_field: str, value: dict) -> bool:
        """Atomically append to an array field in a claim document."""
        filters = {"_id": ObjectId(claim_id), "IsDeleted": False}
        collection = await self._get_collection()
        result = await collection.update_one(
            filters,
            {
                "$push": {array_field: value},
                "$set": {"UpdatedOn": datetime.utcnow()}
            }
        )
        return result.modified_count > 0

    async def get_all_claims(self, skip: int = 0, limit: int = 10) -> List[dict]:
        """Retrieve all claims with pagination."""
        collection = await self._get_collection()
        cursor = collection.find({"IsDeleted": False}).skip(skip).limit(limit).sort("CreatedOn", -1)
        claims = []
        async for doc in cursor:
            claims.append(doc)
        return claims


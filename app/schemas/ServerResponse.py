from pydantic import BaseModel, ConfigDict
from typing import Any, Optional
from bson import ObjectId

class ServerResponse(BaseModel):
    data: Optional[Any] = None
    success: bool
    
    model_config = ConfigDict(
        json_encoders={ObjectId: str},
        json_schema_extra={
            "example": {
                "data": {},
                "success": True
            }
        }
    )

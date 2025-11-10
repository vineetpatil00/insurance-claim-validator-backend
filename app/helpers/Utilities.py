import secrets
from app.schemas.ServerResponse import ServerResponse
from bson import ObjectId
from typing import Any, Dict
from datetime import datetime, timedelta
import jwt
import json
import os

from dotenv import load_dotenv

load_dotenv()

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

class Utils:
    @classmethod
    def generate_hex_string(cls, length=16) -> str:
        """
        Generate a random hexadecimal string of the specified length.

        :param length: Length of the hex string (default is 16 characters).
        :return: Random hexadecimal string.
        """
        return secrets.token_hex(length // 2)
    
    @staticmethod
    def create_jwt_token(
        payload: Dict[str, Any], 
        secret_key: str = None, 
        expires_in: int = None
    ) -> str:
        """
        Create a JWT token.

        :param payload: The payload data to include in the JWT.
        :param secret_key: The secret key for signing the JWT (default: value from environment).
        :param algorithm: The algorithm used for signing (default: RS256).
        :param expires_in: Expiration time in seconds (default: value from environment or 1 hour).
        :return: The generated JWT token.
        """
        # Use default environment variables if not provided
        secret_key = secret_key or os.getenv("JWT_SECRET", "defaultsecret")
        expires_in = expires_in or int(os.getenv("JWT_EXPIRY", 3600))

        # Add exp and iat fields to the payload
        payload_copy = payload.copy()
        payload_copy["exp"] = int((datetime.utcnow() + timedelta(seconds=expires_in)).timestamp())
        payload_copy["iat"] = int(datetime.utcnow().timestamp())

        # Serialize the payload using json.dumps and CustomJSONEncoder
        serialized_payload = json.loads(json.dumps(payload_copy, cls=CustomJSONEncoder))

        # Encode the token
        token = jwt.encode(serialized_payload, secret_key)
        return token

    @classmethod
    def _serialize_data(cls, data: Any) -> Any:
        """
        Recursively serialize data, converting ObjectId to string.

        :param data: The data to serialize.
        :return: Serialized data.
        """
        if isinstance(data, ObjectId):
            return str(data)
        elif isinstance(data, dict):
            return {key: cls._serialize_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [cls._serialize_data(item) for item in data]
        return data

    @classmethod
    def create_response(cls, data: dict, success: bool,error: str = '') -> ServerResponse:
        """
        Create a ServerResponse with serialized data.

        :param data: Data to include in the response.
        :param success: Indicates whether the operation was successful.
        :return: An instance of ServerResponse.
        """
        if not success:
            raise ValueError(error or "An error occurred")
            
        return ServerResponse(
            data=cls._serialize_data(data),
            success=success,
        )
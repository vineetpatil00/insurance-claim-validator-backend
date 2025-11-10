import secrets
from app.schemas.ServerResponse import ServerResponse
from bson import ObjectId
from typing import Any, Dict
import json

from dotenv import load_dotenv

load_dotenv()

class Utils:
    @classmethod
    def generate_hex_string(cls, length=16) -> str:
        """
        Generate a random hexadecimal string of the specified length.

        :param length: Length of the hex string (default is 16 characters).
        :return: Random hexadecimal string.
        """
        return secrets.token_hex(length // 2)
    
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
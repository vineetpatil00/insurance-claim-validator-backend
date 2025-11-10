from bson import ObjectId
from typing import Any
from pydantic_core import core_schema
from pydantic import GetCoreSchemaHandler


class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        def validate(value: Any) -> ObjectId:
            if isinstance(value, ObjectId):
                return value
            if isinstance(value, str):
                if ObjectId.is_valid(value):
                    return ObjectId(value)
                raise ValueError("Invalid ObjectId string")
            raise ValueError("Invalid ObjectId")

        return core_schema.no_info_plain_validator_function(validate)

    @classmethod
    def __get_pydantic_json_schema__(cls, schema, handler):
        # Use the handler to generate the base schema and update it
        json_schema = handler(schema)
        json_schema.update(type="string")
        return json_schema

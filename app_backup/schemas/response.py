from typing import Any, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: T | None = None

# Helpers
def ok(data: Any = None, message: str = "OK") -> dict:
    return {"success": True, "message": message, "data": data}

def fail(message: str) -> dict:
    return {"success": False, "message": message, "data": None}
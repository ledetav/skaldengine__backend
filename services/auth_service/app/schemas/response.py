from typing import Generic, TypeVar, Optional, Any, Dict
from pydantic import BaseModel

T = TypeVar("T")

class BaseResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    error: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

"""Схема стандартизированного API-ответа для всех микросервисов."""

from typing import Any, Optional, TypeVar, Generic
from pydantic import BaseModel, Field

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """Универсальная обёртка ответов API."""

    success: bool = Field(..., description="Флаг успешности выполнения запроса")
    data: Optional[T] = Field(None, description="Полезная нагрузка ответа")
    message: Optional[str] = Field(None, description="Информационное сообщение или описание результата")
    error_code: Optional[str] = Field(None, description="Символьный код ошибки при неуспешном запросе")


"""Базовый контроллер для обработчиков Core Service."""

from typing import Any, Optional
from fastapi import HTTPException, status
from shared.schemas.response import BaseResponse


class BaseController:
    """Базовый класс контроллера для унификации ответов и обработки ошибок."""

    def handle_success(self, data: Any = None, meta: Optional[dict] = None) -> BaseResponse:
        """Формирует успешный ответ."""
        return BaseResponse(success=True, data=data)

    def handle_error(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        """Возбуждает HTTP-исключение с заданным кодом и сообщением."""
        raise HTTPException(status_code=status_code, detail=message)


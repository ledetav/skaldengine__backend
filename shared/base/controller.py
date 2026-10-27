"""Базовый контроллер для сервисов приложения."""

from typing import Any, Optional
from fastapi import HTTPException, status
from shared.schemas.response import BaseResponse


class BaseController:
    """Базовый класс контроллера, предоставляющий стандартные методы формирования ответов."""

    def handle_success(self, data: Any = None, message: str = "Операция успешно выполнена") -> BaseResponse:
        """Формирует успешный ответ в стандартном формате BaseResponse.

        Args:
            data: Данные для включения в ответ.
            message: Текстовое сообщение об успешном выполнении.

        Returns:
            BaseResponse: Экземпляр схемы ответа с флагом success=True.
        """
        return BaseResponse(
            success=True,
            data=data,
            message=message
        )

    def handle_error(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, error_code: Optional[str] = None):
        """Возбуждает HTTP-исключение с унифицированным форматом ошибки.

        Args:
            message: Текстовое описание ошибки.
            status_code: HTTP-статус код ошибки (по умолчанию 400).
            error_code: Необязательный символьный код ошибки.

        Raises:
            HTTPException: Исключение FastAPI с деталями ошибки.
        """
        raise HTTPException(
            status_code=status_code,
            detail={
                "success": False,
                "message": message,
                "error_code": error_code
            }
        )


"""Middleware для логирования входящих HTTP-запросов и глобальной обработки ошибок."""

import logging
import time
import traceback
from fastapi import Request, FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware для фиксации времени выполнения и логирования каждого HTTP-запроса."""

    async def dispatch(self, request: Request, call_next):
        """Перехватывает запрос, измеряет время его обработки и логирует результат."""
        start_time = time.time()
        # Логирование входящего запроса
        logger.info(f"Received request: {request.method} {request.url.path}")
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            # Логирование успешного завершения запроса
            logger.info(f"Completed request: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.4f}s")
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"Failed request: {request.method} {request.url.path} - Exception: {e} - Time: {process_time:.4f}s", exc_info=True)
            raise e


def add_global_exception_handler(app: FastAPI):
    """Регистрирует глобальный обработчик необработанных исключений для экземпляра FastAPI.

    Args:
        app: Экземпляр приложения FastAPI.
    """
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Внутренний обработчик необработанных исключений сервера с форматированным выводом трейсбека."""
        print(f"\n{'='*50}\n🔥 КРИТИЧЕСКАЯ ОШИБКА 🔥")
        traceback.print_exc()
        print(f"{'='*50}\n")
        logger.error(f"Unhandled exception during {request.method} {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"}
        )


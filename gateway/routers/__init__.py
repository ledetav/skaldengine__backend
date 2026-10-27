"""Пакет маршрутизаторов API Gateway.

Объединяет системные эндпоинты проверки состояния и маршруты интерактивной документации.
"""
from gateway.routers.system import router as system_router
from gateway.routers.docs import router as docs_router

__all__ = ["system_router", "docs_router"]

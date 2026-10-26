"""Роутер Swagger UI и OpenAPI-спецификаций микросервисов.

Предоставляет объединенный доступ к интерактивной документации:
- /auth/docs — документация Auth Service
- /core/docs — документация Core Service
"""
from fastapi import APIRouter, Request
from fastapi.responses import Response

from gateway.config import AUTH_BASE, CORE_BASE
from gateway.proxy import _proxy, _proxy_docs

router = APIRouter()


@router.get("/auth/docs", include_in_schema=False)
async def auth_docs(request: Request) -> Response:
    """Отображение страницы Swagger UI для Auth Service."""
    return await _proxy_docs(
        docs_path="/docs",
        openapi_path="/api/v1/openapi.json",
        target_base=AUTH_BASE,
        prefix="auth",
        request=request,
    )


@router.get("/auth/api/v1/openapi.json", include_in_schema=False)
async def auth_openapi(request: Request) -> Response:
    """Проксирование схемы OpenAPI для Auth Service."""
    return await _proxy("/api/v1/openapi.json", AUTH_BASE, request)


@router.get("/core/docs", include_in_schema=False)
async def core_docs(request: Request) -> Response:
    """Отображение страницы Swagger UI для Core Service."""
    return await _proxy_docs(
        docs_path="/docs",
        openapi_path="/api/v1/openapi.json",
        target_base=CORE_BASE,
        prefix="core",
        request=request,
    )


@router.get("/core/api/v1/openapi.json", include_in_schema=False)
async def core_openapi(request: Request) -> Response:
    """Проксирование схемы OpenAPI для Core Service."""
    return await _proxy("/api/v1/openapi.json", CORE_BASE, request)

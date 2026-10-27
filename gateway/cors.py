"""Модуль управления политикой CORS для API Gateway.

Обеспечивает валидацию заголовка Origin с защитой от спуфинга поддоменов
и обработку preflight OPTIONS-запросов.
"""
import os
import json
from urllib.parse import urlsplit
from fastapi import Request
from fastapi.responses import Response


def get_env_list(key: str, default: list) -> list:
    """Безопасно извлекает список разрешенных хостов из переменных окружения."""
    raw = os.getenv(key, "")
    if not raw:
        return default
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else [data]
    except Exception:
        return [raw]


def is_origin_allowed(origin: str, allowed_origins: list, allowed_suffixes: list) -> bool:
    """
    Проверяет валидность Origin с защитой от подмены доменов (phishing / SSRF).
    """
    if not origin:
        return False
    if origin in allowed_origins:
        return True
    try:
        parsed = urlsplit(origin)
        hostname = (parsed.hostname or "").lower()
    except Exception:
        return False

    if not hostname:
        return False

    if hostname in allowed_origins or hostname in ("localhost", "127.0.0.1"):
        return True

    for suffix in allowed_suffixes:
        clean_suffix = suffix.lower()
        if clean_suffix in ("localhost", "127.0.0.1"):
            if hostname == clean_suffix:
                return True
        else:
            if not clean_suffix.startswith("."):
                clean_suffix = "." + clean_suffix
            if hostname.endswith(clean_suffix):
                return True

    return False


async def cors_middleware(request: Request, call_next):
    """
    CORS middleware с поддержкой динамических параметров и предзапросов OPTIONS.
    """
    origin = request.headers.get("origin", "")

    # Считываем настройки на каждый запрос (поддержка динамических Replit Secrets)
    allowed_origins = get_env_list("BACKEND_CORS_ORIGINS", [])
    allowed_suffixes = get_env_list(
        "BACKEND_CORS_ALLOWED_SUFFIXES",
        [".replit.dev", ".replit.app", "localhost", "127.0.0.1"]
    )

    is_allowed = is_origin_allowed(origin, allowed_origins, allowed_suffixes)

    # Обработка preflight OPTIONS
    if request.method == "OPTIONS":
        response = Response(status_code=200)
        if is_allowed:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Access-Control-Max-Age"] = "600"
        return response

    response = await call_next(request)

    if is_allowed:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"

    return response

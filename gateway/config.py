"""Конфигурация шлюза API Gateway.

Определяет URL-адреса целевых микросервисов (Auth Service, Core Service),
префиксы маршрутизации и настройки логирования.
"""
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("gateway")

# Базовые адреса целевых микросервисов
AUTH_BASE = os.getenv("AUTH_BASE_URL", "http://127.0.0.1:8001")
CORE_BASE = os.getenv("CORE_BASE_URL", "http://127.0.0.1:8000")

# Префиксы эндпоинтов, перенаправляемых в Auth Service (все остальные идут в Core Service)
AUTH_PREFIXES = ("/api/v1/auth", "/api/v1/users")

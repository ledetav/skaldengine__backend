"""Точка входа и инициализация микросервиса бизнес-логики и ИИ (Core Service)."""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.api import api_router
from shared.logging_config import setup_logging
from shared.middlewares.logging_middleware import LoggingMiddleware, add_global_exception_handler

setup_logging(settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения FastAPI."""
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)
add_global_exception_handler(app)

# Раздача статики (загруженные медиафайлы и изображения)
app.mount("/static", StaticFiles(directory=settings.UPLOAD_DIR), name="static")

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
def health_check():
    """Проверка жизнеспособности сервиса Core Service."""
    return {"status": "ok", "service": "core-service"}
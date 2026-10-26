"""Конфигурация настроек микросервиса Core Service."""

import os
from pydantic import Field, AliasChoices, field_validator
from typing import List, Union, Any
import json
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки окружения Core Service (БД, Polza.ai, пути загрузки файлов)."""

    PROJECT_NAME: str = Field("SkaldEngine Core Service", validation_alias=AliasChoices("CORE_PROJECT_NAME", "PROJECT_NAME"))
    API_V1_STR: str = "/api/v1"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    # Подключение к PostgreSQL (asyncpg)
    DATABASE_URL: str = Field(validation_alias=AliasChoices("CORE_DATABASE_URL", "DATABASE_URL"))

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def make_async_url(cls, v: Any) -> Any:
        """Приводит URL базы данных PostgreSQL к асинхронному драйверу postgresql+asyncpg."""
        if isinstance(v, str) and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    AUTH_BASE_URL: str = Field("http://auth:8001", validation_alias="AUTH_BASE_URL")

    # Настройки интеграции с Polza.ai (OpenAI-совместимый шлюз)
    POLZA_API_KEY: str = Field(..., description="Системный API-ключ Polza.ai")
    POLZA_CHAT_MODEL: str = Field("openai/gpt-4o", description="Модель для генерации ответов персонажей")
    POLZA_EMBEDDING_MODEL: str = Field("openai/text-embedding-3-small", description="Модель для векторных эмбеддингов")
    POLZA_SUMMARY_MODEL: str = Field("openai/gpt-4o-mini", description="Модель для суммаризации истории диалога")
    POLZA_TITLE_MODEL: str = Field("google/gemini-2.0-flash-lite-preview-02-05", description="Модель для генерации названий чатов")
    POLZA_TEMPERATURE: float = Field(1.0, description="Температура генерации текста")
    POLZA_MAX_TOKENS: int = Field(8000, description="Максимальное количество токенов ответа")
    POLZA_TITLE_MAX_TOKENS: int = Field(50, description="Максимальное количество токенов для генерации заголовка")
    POLZA_RAG_MAX_DISTANCE: float = Field(0.60, description="Максимальное косинусное расстояние для RAG-поиска")

    # Директория загрузки медиафайлов (аватары, карточки персонажей)
    UPLOAD_DIR: str = Field("./uploads", validation_alias=AliasChoices("CORE_UPLOAD_DIR", "UPLOAD_DIR"))

    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8001",
        "http://localhost:8080",
    ]

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding='utf-8', 
        case_sensitive=True, 
        extra="ignore"
    )


settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
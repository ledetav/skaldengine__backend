import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "SkaldEngine Core Service"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    # PostgreSQL (asyncpg)
    DATABASE_URL: str

    # Redis (ARQ broker + cache)
    REDIS_URL: str = "redis://localhost:6379"

    # Polza.ai (OpenAI wrapper)
    POLZA_API_KEY: str
    POLZA_CHAT_MODEL: str = "openai/gpt-4o"
    POLZA_EMBEDDING_MODEL: str = "openai/text-embedding-3-small"
    POLZA_SUMMARY_MODEL: str = "openai/gpt-4o-mini"
    POLZA_TEMPERATURE: float = 1.0
    POLZA_MAX_TOKENS: int = 8000

    # Uploads (аватарки, карточки)
    UPLOAD_DIR: str = "./uploads"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
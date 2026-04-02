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

    # Google Gemini / Vertex AI
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-1.5-flash-001"
    GEMINI_TEMPERATURE: float = 1.0
    GEMINI_MAX_TOKENS: int = 8000

    GEMINI_MAX_TOKENS: int = 8000

    # Uploads (аватарки, карточки)
    UPLOAD_DIR: str = "./uploads"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
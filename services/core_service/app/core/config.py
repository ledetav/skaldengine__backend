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

    # Vertex AI (опциональные — для прямой работы с Vertex API)
    VERTEX_PROJECT_ID: str = ""
    VERTEX_LOCATION: str = "us-central1"

    # Uploads (аватарки, карточки)
    UPLOAD_DIR: str = "./uploads"

    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_EVENTS: str = "skaldenginebackend_entity_events"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
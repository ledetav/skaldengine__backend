import os
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = Field("SkaldEngine Core Service", validation_alias=AliasChoices("CORE_PROJECT_NAME", "PROJECT_NAME"))
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    # PostgreSQL (asyncpg)
    DATABASE_URL: str = Field(validation_alias=AliasChoices("CORE_DATABASE_URL", "DATABASE_URL"))


    # Polza.ai (OpenAI wrapper)
    POLZA_API_KEY: str
    POLZA_CHAT_MODEL: str = "openai/gpt-4o"
    POLZA_EMBEDDING_MODEL: str = "openai/text-embedding-3-small"
    POLZA_SUMMARY_MODEL: str = "openai/gpt-4o-mini"
    POLZA_TITLE_MODEL: str = "google/gemini-2.0-flash-lite-preview-02-05"
    POLZA_TEMPERATURE: float = 1.0
    POLZA_MAX_TOKENS: int = 8000
    POLZA_TITLE_MAX_TOKENS: int = 50

    # Uploads (аватарки, карточки)
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
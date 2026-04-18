import os
from pydantic import Field, AliasChoices, field_validator
from typing import List, Union
import json
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

    BACKEND_CORS_ORIGINS: Union[List[str], str] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, str) and v.startswith("["):
            try:
                return json.loads(v)
            except Exception:
                pass
        elif isinstance(v, list):
            return v
        return v

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding='utf-8', 
        case_sensitive=True, 
        extra="ignore"
    )


settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
from pydantic import Field, AliasChoices, field_validator
from typing import List, Union, Any
import json
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = Field("SkaldEngine Auth Service", validation_alias=AliasChoices("AUTH_PROJECT_NAME", "PROJECT_NAME"))
    API_V1_STR: str = "/api/v1"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str = Field(validation_alias=AliasChoices("AUTH_DATABASE_URL", "DATABASE_URL"))

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def make_async_url(cls, v: Any) -> Any:
        if isinstance(v, str) and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

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
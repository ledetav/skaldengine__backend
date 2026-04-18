from pydantic import Field, AliasChoices, field_validator
from typing import List, Union
import json
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = Field("SkaldEngine Auth Service", validation_alias=AliasChoices("AUTH_PROJECT_NAME", "PROJECT_NAME"))
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str = Field(validation_alias=AliasChoices("AUTH_DATABASE_URL", "DATABASE_URL"))

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
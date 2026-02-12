from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Roleplay Platform"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "super-secret-key-for-dev"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_URL: str = "sqlite+aiosqlite:///./diploma.db"
    UPLOAD_DIR: str = "app/static/uploads"
    GEMINI_API_KEY: str
    CHROMA_DB_PATH: str = "./chroma_db"
    
    # Читаем из .env, игнорируем лишние переменные
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)
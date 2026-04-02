from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class EpisodicMemoryBase(BaseModel):
    summary: str


class EpisodicMemoryCreate(EpisodicMemoryBase):
    """Используется при создании записи памяти (обычно через background task)."""
    message_id: UUID
    embedding: list[float]  # 768-dim вектор

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "summary": "User recalled a lost memory about a wooden toy.",
                    "message_id": "123e4567-e89b-12d3-a456-426614174003",
                    "embedding": [0.1, 0.2, 0.3]
                }
            ]
        }
    }


class EpisodicMemory(EpisodicMemoryBase):
    id: UUID
    chat_id: UUID
    message_id: UUID

    class Config:
        from_attributes = True

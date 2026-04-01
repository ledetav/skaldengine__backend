from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class EpisodicMemoryBase(BaseModel):
    summary: str


class EpisodicMemoryCreate(EpisodicMemoryBase):
    """Используется при создании записи памяти (обычно через background task)."""
    message_id: UUID
    embedding: list[float]  # 768-dim вектор


class EpisodicMemory(EpisodicMemoryBase):
    id: UUID
    chat_id: UUID
    message_id: UUID

    class Config:
        from_attributes = True

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class MessageBase(BaseModel):
    role: str
    content: str


class MessageCreate(BaseModel):
    """Входящее сообщение от пользователя."""
    content: str
    parent_id: UUID | None = None  # Для ветвления (swipe)


class MessageRegenerate(BaseModel):
    """Запрос на перегенерацию ответа."""
    message_id: UUID


class Message(MessageBase):
    id: UUID
    chat_id: UUID
    parent_id: UUID | None = None
    hidden_thought: str | None = None
    is_edited: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

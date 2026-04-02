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

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "content": "Hello there! How are you doing today?",
                    "parent_id": "123e4567-e89b-12d3-a456-426614174000"
                }
            ]
        }
    }


class MessageRegenerate(BaseModel):
    """Запрос на перегенерацию ответа."""
    message_id: UUID

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message_id": "123e4567-e89b-12d3-a456-426614174000"
                }
            ]
        }
    }


class Message(MessageBase):
    id: UUID
    chat_id: UUID
    parent_id: UUID | None = None
    hidden_thought: str | None = None
    is_edited: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

"""
Pydantic-схемы для работы с сообщениями чата (Message).
"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class MessageBase(BaseModel):
    """Базовые атрибуты сообщения."""
    role: str = Field(..., description="Роль отправителя: user, assistant или system")
    content: str = Field(..., max_length=4000, description="Текст сообщения")


class MessageCreate(BaseModel):
    """Входящее сообщение от пользователя с поддержкой ветвления (parent_id)."""
    content: str = Field(..., max_length=4000, description="Текст сообщения пользователя")
    parent_id: UUID | None = Field(default=None, description="ID родительского сообщения для ветвления")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "content": "Привет! Как твои дела?",
                    "parent_id": "123e4567-e89b-12d3-a456-426614174000"
                }
            ]
        }
    }


class MessageRegenerate(BaseModel):
    """Запрос на перегенерацию ответа (свайп)."""
    message_id: UUID = Field(..., description="ID сообщения пользователя для генерации альтернативного ответа")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message_id": "123e4567-e89b-12d3-a456-426614174000"
                }
            ]
        }
    }


class MessageResponse(MessageBase):
    """Схема ответа с данными сообщения."""
    id: UUID
    chat_id: UUID
    parent_id: UUID | None = None
    hidden_thought: str | None = None
    is_edited: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


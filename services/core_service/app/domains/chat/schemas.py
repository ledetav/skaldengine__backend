"""
Pydantic-схемы для работы с ролевыми чатами (Chat).
"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class ChatBase(BaseModel):
    """Базовые атрибуты ролевого чата."""
    character_id: UUID = Field(..., description="ID персонажа")
    user_persona_id: UUID = Field(..., description="ID персоны пользователя")
    scenario_id: UUID | None = Field(default=None, description="ID сценария (опционально)")
    title: str | None = Field(default=None, description="Название чата")
    is_acquainted: bool = Field(default=False, description="Флаг знакомства персонажей")
    relationship_dynamic: str | None = Field(default=None, description="Динамика взаимоотношений")
    custom_location: str | None = Field(default=None, description="Кастомная локация")
    custom_plot_hook: str | None = Field(default=None, description="Кастомная сюжетная завязка")
    language: str = Field(default="ru", description="Язык повествования")
    narrative_voice: str = Field(default="third", description="Лицо повествования: first, second или third")
    persona_lorebook_id: UUID | None = Field(default=None, description="ID лорбука персоны")
    checkpoints_count: int = Field(default=3, ge=2, le=6, description="Количество сюжетных чекпоинтов (2-6)")


class ChatCreate(ChatBase):
    """Схема создания нового ролевого чата."""
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "character_id": "123e4567-e89b-12d3-a456-426614174000",
                    "user_persona_id": "123e4567-e89b-12d3-a456-426614174001",
                    "persona_lorebook_id": "123e4567-e89b-12d3-a456-426614174005",
                    "scenario_id": "123e4567-e89b-12d3-a456-426614174002",
                    "is_acquainted": True,
                    "relationship_dynamic": "Соперники, вынужденные сотрудничать",
                    "language": "ru",
                    "narrative_voice": "third"
                }
            ]
        }
    }


class ChatUpdate(BaseModel):
    """Схема обновления параметров чата."""
    title: str | None = Field(default=None, description="Название")
    language: str | None = Field(default=None, description="Язык")
    narrative_voice: str | None = Field(default=None, description="Лицо повествования")
    is_acquainted: bool | None = Field(default=None, description="Флаг знакомства")
    relationship_dynamic: str | None = Field(default=None, description="Динамика отношений")
    persona_lorebook_id: UUID | None = Field(default=None, description="ID лорбука персоны")
    active_leaf_id: UUID | None = Field(default=None, description="ID активного сообщения ветки")


class ChatResponse(ChatBase):
    """Схема ответа с данными чата и обогащенными полями для списка."""
    id: UUID
    user_id: UUID
    mode: str
    active_leaf_id: UUID | None = None
    created_at: datetime
    updated_at: datetime | None = None
    
    # Обогащенные поля для отображения в каталоге/списке чатов
    character_name: str | None = None
    user_persona_name: str | None = None
    last_message_preview: str | None = None

    model_config = ConfigDict(from_attributes=True)


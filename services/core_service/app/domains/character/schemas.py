"""
Pydantic-схемы для работы с персонажами (Character).
"""

from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from app.domains.character.models import CharacterType


class CharacterBase(BaseModel):
    """Базовые атрибуты персонажа."""
    name: str = Field(..., max_length=200, description="Имя персонажа")
    description: str | None = Field(default=None, max_length=500, description="Краткое описание")
    type: CharacterType = Field(default=CharacterType.FANDOM, description="Тип: fandom или original")
    fandom: str | None = Field(default=None, max_length=200, description="Фандом/вселенная")
    avatar_url: str | None = Field(default=None, description="URL аватара")
    card_image_url: str | None = Field(default=None, description="URL карточки персонажа")
    appearance: str | None = Field(default=None, max_length=2000, description="Описание внешности")
    personality: str | None = Field(default=None, max_length=2000, description="Описание характера и манеры общения")
    is_public: bool = Field(default=False, description="Флаг публичной видимости в каталоге")
    gender: str | None = Field(default=None, max_length=100, description="Гендер/пол")
    age: str | None = Field(default=None, max_length=100, description="Возраст персонажа")
    nsfw_allowed: bool = Field(default=True, description="Разрешен ли контент 18+")
    lorebook_ids: List[UUID] | None = Field(default=None, description="Список ID привязанных лорбуков")


class CharacterCreate(CharacterBase):
    """Схема создания нового персонажа."""
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Древний",
                    "description": "Древнее существо космического ужаса.",
                    "type": "fandom",
                    "fandom": "Мифы Ктулху",
                    "avatar_url": "https://example.com/avatar.jpg",
                    "card_image_url": "https://example.com/card.jpg",
                    "appearance": "Щупальца, формирующие призрачную массу",
                    "personality": "Непостижимый, холодный, безразличный",
                    "is_public": True,
                    "gender": "other",
                    "nsfw_allowed": True,
                    "lorebook_ids": []
                }
            ]
        }
    }


class CharacterUpdate(BaseModel):
    """Схема частичного обновления данных персонажа."""
    name: str | None = Field(default=None, max_length=200, description="Имя")
    description: str | None = Field(default=None, max_length=500, description="Краткое описание")
    type: CharacterType | None = Field(default=None, description="Тип персонажа")
    fandom: str | None = Field(default=None, max_length=200, description="Фандом")
    avatar_url: str | None = Field(default=None, description="URL аватара")
    card_image_url: str | None = Field(default=None, description="URL карточки")
    appearance: str | None = Field(default=None, max_length=2000, description="Внешность")
    personality: str | None = Field(default=None, max_length=2000, description="Личность")
    is_public: bool | None = Field(default=None, description="Публичный статус")
    gender: str | None = Field(default=None, max_length=100, description="Гендер")
    age: str | None = Field(default=None, max_length=100, description="Возраст")
    nsfw_allowed: bool | None = Field(default=None, description="Разрешен ли 18+ контент")
    lorebook_ids: List[UUID] | None = Field(default=None, description="ID привязанных лорбуков")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Древний (Обновленный)",
                    "description": "Обновленное описание",
                    "type": "original",
                    "fandom": None,
                    "avatar_url": "https://example.com/avatar_new.jpg",
                    "card_image_url": "https://example.com/card_new.jpg",
                    "appearance": "Еще больше щупалец",
                    "personality": "Еще более безразличный",
                    "is_public": False,
                    "gender": "other",
                    "nsfw_allowed": False,
                    "lorebook_ids": ["123e4567-e89b-12d3-a456-426614174000"]
                }
            ]
        }
    }


class CharacterRead(BaseModel):
    """Публичная схема персонажа для чтения."""
    id: UUID
    name: str
    description: str | None = None
    type: CharacterType
    fandom: str | None = None
    avatar_url: str | None = None
    card_image_url: str | None = None
    is_public: bool
    gender: str | None = None
    age: str | None = None
    nsfw_allowed: bool
    total_chats_count: int
    monthly_chats_count: int
    creator_id: Optional[UUID] = None
    scenarios_count: int = 0
    scenario_chats_count: int = 0
    lorebook_ids: List[UUID] = []
    author: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def model_validate(cls, obj, **kwargs):
        if hasattr(obj, 'lorebooks'):
            setattr(obj, 'lorebook_ids', [lb.id for lb in obj.lorebooks])
        return super().model_validate(obj, **kwargs)


class CharacterAdminRead(CharacterRead):
    """Административная схема персонажа (включает системные промпты внешности и характера)."""
    appearance: str | None = None
    personality: str | None = None
    creator_id: UUID | None = None


# Общий внутренний класс персонажа
class Character(CharacterBase):
    """Внутренняя схема персонажа с полным набором счетчиков."""
    id: UUID
    creator_id: UUID | None = None
    total_chats_count: int
    monthly_chats_count: int
    scenarios_count: int = 0
    scenario_chats_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# Псевдонимы схем ответов API
CharacterResponse = CharacterRead


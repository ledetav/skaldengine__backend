"""
Pydantic-схемы для работы со справочниками мира (Lorebook) и их записями (LorebookEntry).
"""

from typing import Annotated
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from app.domains.lorebook.models import LorebookType


# ─── LorebookEntry ─────────────────────────────────────────────────────────── #

class LorebookEntryBase(BaseModel):
    """Базовые атрибуты записи справочника мира."""
    keywords: list[Annotated[str, Field(max_length=150)]] = Field(
        default=[],
        max_length=10,
        description="Ключевые слова-триггеры для лексического поиска"
    )
    content: str = Field(..., max_length=2000, description="Текст лор-факта или описания")
    priority: int = Field(default=0, description="Приоритет вставки в контекст (чем выше, тем раньше)")
    category: str = Field(default="general", description="Категория: fact, appearance, mindset, speech, inventory, secret")
    is_always_included: bool = Field(default=False, description="Всегда включать в промпт вне зависимости от триггеров")


class LorebookEntryCreate(LorebookEntryBase):
    """Схема создания записи справочника."""
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "keywords": ["магия", "заклинание", "чародей"],
                    "content": "Магия черпается из эфира вокруг заклинателя.",
                    "priority": 10
                }
            ]
        }
    }


class LorebookEntryBulkCreate(BaseModel):
    """Схема пакетного создания записей справочника."""
    entries: list[LorebookEntryCreate]


class LorebookEntryUpdate(BaseModel):
    """Схема частичного обновления записи справочника."""
    keywords: list[Annotated[str, Field(max_length=150)]] | None = Field(default=None, max_length=10, description="Ключевые слова")
    content: str | None = Field(default=None, max_length=2000, description="Текст записи")
    priority: int | None = Field(default=None, description="Приоритет")
    category: str | None = Field(default=None, description="Категория")
    is_always_included: bool | None = Field(default=None, description="Флаг обязательного включения")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "keywords": ["магия", "заклинание", "чародей", "волшебник"],
                    "content": "Магия черпается из эфира. Требует предельной концентрации.",
                    "priority": 20
                }
            ]
        }
    }


class LorebookEntry(LorebookEntryBase):
    """Схема чтения записи лорбука с ID."""
    id: UUID
    lorebook_id: UUID

    model_config = ConfigDict(from_attributes=True)


# ─── Lorebook ──────────────────────────────────────────────────────────────── #

class LorebookBase(BaseModel):
    """Базовые атрибуты лорбука."""
    name: str = Field(..., max_length=200, description="Название лорбука")
    type: LorebookType = Field(default=LorebookType.FANDOM, description="Тип: fandom, character или persona")
    character_id: UUID | None = Field(default=None, description="ID связанного персонажа")
    user_persona_id: UUID | None = Field(default=None, description="ID связанной персоны")
    fandom: str | None = Field(default=None, max_length=200, description="Название фандома")
    description: str | None = Field(default=None, max_length=500, description="Описание лорбука")
    category: str = Field(default="general", description="Категория")
    tags: list[str] = Field(default=[], description="Список тегов")


class LorebookCreate(LorebookBase):
    """Схема создания нового лорбука."""
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Хроники магии",
                    "character_id": "aa3e4567-e89b-12d3-a456-426614174003",
                    "fandom": "Fantasy Realm"
                },
                {
                    "name": "Личный дневник",
                    "user_persona_id": "123e4567-e89b-12d3-a456-426614174001"
                }
            ]
        }
    }


class LorebookUpdate(BaseModel):
    """Схема частичного обновления метаданных лорбука."""
    name: str | None = Field(default=None, max_length=200, description="Название")
    description: str | None = Field(default=None, max_length=500, description="Описание")
    type: LorebookType | None = Field(default=None, description="Тип лорбука")
    fandom: str | None = Field(default=None, max_length=200, description="Фандом")
    character_id: UUID | None = Field(default=None, description="ID персонажа")
    user_persona_id: UUID | None = Field(default=None, description="ID персоны")
    category: str | None = Field(default=None, description="Категория")
    tags: list[str] | None = Field(default=None, description="Теги")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Хроники магии: Расширенное издание",
                    "fandom": "High Fantasy Realm"
                }
            ]
        }
    }


class Lorebook(LorebookBase):
    """Схема лорбука с количеством записей."""
    id: UUID
    entries_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class LorebookWithEntries(Lorebook):
    """Схема лорбука со списком всех его записей."""
    entries: list[LorebookEntry] = []



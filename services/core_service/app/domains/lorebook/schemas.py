from pydantic import BaseModel, Field
from typing import Annotated
from uuid import UUID


# ─── LorebookEntry ─────────────────────────────────────────────────────────── #

class LorebookEntryBase(BaseModel):
    keywords: list[Annotated[str, Field(max_length=150)]] = Field(default=[], max_length=10)
    content: str = Field(..., max_length=2000)
    priority: int = 0
    category: str = "general"
    is_always_included: bool = False


class LorebookEntryCreate(LorebookEntryBase):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "keywords": ["magic", "spell", "wizard"],
                    "content": "Magic is drawn from the aether around the caster.",
                    "priority": 10
                }
            ]
        }
    }


class LorebookEntryBulkCreate(BaseModel):
    entries: list[LorebookEntryCreate]


class LorebookEntryUpdate(BaseModel):
    keywords: list[Annotated[str, Field(max_length=150)]] | None = Field(default=None, max_length=10)
    content: str | None = Field(default=None, max_length=2000)
    priority: int | None = None
    category: str | None = None
    is_always_included: bool | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "keywords": ["magic", "spell", "wizard", "sorcerer"],
                    "content": "Magic is drawn from the aether. It requires extreme focus.",
                    "priority": 20
                }
            ]
        }
    }


class LorebookEntry(LorebookEntryBase):
    id: UUID
    lorebook_id: UUID

    class Config:
        from_attributes = True


# ─── Lorebook ──────────────────────────────────────────────────────────────── #

from app.domains.lorebook.models import LorebookType

class LorebookBase(BaseModel):
    name: str = Field(..., max_length=200)
    type: LorebookType = LorebookType.FANDOM
    character_id: UUID | None = None
    user_persona_id: UUID | None = None
    fandom: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    category: str = "general"
    tags: list[str] = []


class LorebookCreate(LorebookBase):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Chronicles of Magic",
                    "character_id": "aa3e4567-e89b-12d3-a456-426614174003",
                    "fandom": "Fantasy Realm"
                },
                {
                    "name": "Personal Journal",
                    "user_persona_id": "123e4567-e89b-12d3-a456-426614174001"
                }
            ]
        }
    }


class LorebookUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    type: LorebookType | None = None
    fandom: str | None = Field(default=None, max_length=200)
    character_id: UUID | None = None
    user_persona_id: UUID | None = None
    category: str | None = None
    tags: list[str] | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Chronicles of Magic: Extended Version",
                    "fandom": "High Fantasy Realm"
                }
            ]
        }
    }


class Lorebook(LorebookBase):
    id: UUID
    entries_count: int = 0

    class Config:
        from_attributes = True


class LorebookWithEntries(Lorebook):
    entries: list[LorebookEntry] = []


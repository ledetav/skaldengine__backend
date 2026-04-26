from pydantic import BaseModel
from uuid import UUID


# ─── LorebookEntry ─────────────────────────────────────────────────────────── #

class LorebookEntryBase(BaseModel):
    keywords: list[str] = []
    content: str
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
    keywords: list[str] | None = None
    content: str | None = None
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
    name: str
    type: LorebookType = LorebookType.FANDOM
    character_id: UUID | None = None
    user_persona_id: UUID | None = None
    fandom: str | None = None
    description: str | None = None
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
    name: str | None = None
    description: str | None = None
    type: LorebookType | None = None
    fandom: str | None = None
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


from pydantic import BaseModel
from uuid import UUID


# ─── LorebookEntry ─────────────────────────────────────────────────────────── #

class LorebookEntryBase(BaseModel):
    keywords: list[str] = []
    content: str
    priority: int = 0


class LorebookEntryCreate(LorebookEntryBase):
    pass


class LorebookEntryUpdate(BaseModel):
    keywords: list[str] | None = None
    content: str | None = None
    priority: int | None = None


class LorebookEntry(LorebookEntryBase):
    id: UUID
    lorebook_id: UUID

    class Config:
        from_attributes = True


# ─── Lorebook ──────────────────────────────────────────────────────────────── #

class LorebookBase(BaseModel):
    name: str
    character_id: UUID | None = None
    fandom: str | None = None


class LorebookCreate(LorebookBase):
    pass


class LorebookUpdate(BaseModel):
    name: str | None = None
    fandom: str | None = None


class Lorebook(LorebookBase):
    id: UUID
    entries: list[LorebookEntry] = []

    class Config:
        from_attributes = True

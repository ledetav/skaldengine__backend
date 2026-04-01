from pydantic import BaseModel
from uuid import UUID


# ─── CharacterAttribute ────────────────────────────────────────────────────── #

class CharacterAttributeBase(BaseModel):
    category: str = "fact"  # "fact" | "speech_example" | "mindset" | "bio"
    content: str


class CharacterAttributeCreate(CharacterAttributeBase):
    pass


class CharacterAttributeUpdate(BaseModel):
    category: str | None = None
    content: str | None = None


class CharacterAttribute(CharacterAttributeBase):
    id: UUID
    character_id: UUID

    class Config:
        from_attributes = True

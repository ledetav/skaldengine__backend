from pydantic import BaseModel
from uuid import UUID


class CharacterBase(BaseModel):
    name: str
    description: str | None = None
    fandom: str | None = None
    avatar_url: str | None = None
    card_image_url: str | None = None
    appearance: str | None = None
    personality: str | None = None
    is_public: bool = False


class CharacterCreate(CharacterBase):
    pass


class CharacterUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    fandom: str | None = None
    avatar_url: str | None = None
    card_image_url: str | None = None
    appearance: str | None = None
    personality: str | None = None
    is_public: bool | None = None


class Character(CharacterBase):
    id: UUID
    creator_id: UUID | None = None

    class Config:
        from_attributes = True

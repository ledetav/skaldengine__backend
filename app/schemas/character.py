from pydantic import BaseModel
from uuid import UUID

class CharacterBase(BaseModel):
    name: str
    avatar_url: str | None = None
    appearance: str
    personality_traits: str
    speech_style: str
    inner_world: str | None = None
    behavioral_cues: str | None = None

class CharacterCreate(CharacterBase):
    pass

class CharacterUpdate(BaseModel):
    name: str | None = None
    avatar_url: str | None = None
    appearance: str | None = None
    personality_traits: str | None = None
    speech_style: str | None = None
    inner_world: str | None = None
    behavioral_cues: str | None = None

class Character(CharacterBase):
    id: UUID

    class Config:
        from_attributes = True

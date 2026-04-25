from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from app.domains.character.models import CharacterType

class CharacterBase(BaseModel):
    name: str
    description: str | None = None
    type: CharacterType = CharacterType.FANDOM
    fandom: str | None = None
    avatar_url: str | None = None
    card_image_url: str | None = None
    appearance: str | None = None
    personality: str | None = None
    is_public: bool = False
    # Новые поля
    gender: str | None = None
    nsfw_allowed: bool = True
    lorebook_ids: List[UUID] | None = None


class CharacterCreate(CharacterBase):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Eldritch",
                    "description": "An ancient being of cosmic horror.",
                    "type": "fandom",
                    "fandom": "Cthulhu Mythos",
                    "avatar_url": "https://example.com/avatar.jpg",
                    "card_image_url": "https://example.com/card.jpg",
                    "appearance": "Tentacles forming a spectral mass",
                    "personality": "Unfathomable, cold, indifferent",
                    "is_public": True,
                    "gender": "other",
                    "nsfw_allowed": True,
                    "lorebook_ids": []
                }
            ]
        }
    }


class CharacterUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    type: CharacterType | None = None
    fandom: str | None = None
    avatar_url: str | None = None
    card_image_url: str | None = None
    appearance: str | None = None
    personality: str | None = None
    is_public: bool | None = None
    gender: str | None = None
    nsfw_allowed: bool | None = None
    lorebook_ids: List[UUID] | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Eldritch (Updated)",
                    "description": "Updated description",
                    "type": "original",
                    "fandom": None,
                    "avatar_url": "https://example.com/avatar_new.jpg",
                    "card_image_url": "https://example.com/card_new.jpg",
                    "appearance": "More tentacles",
                    "personality": "Even more indifferent",
                    "is_public": False,
                    "gender": "other",
                    "nsfw_allowed": False,
                    "lorebook_ids": ["123e4567-e89b-12d3-a456-426614174000"]
                }
            ]
        }
    }


class CharacterRead(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    type: CharacterType
    fandom: str | None = None
    avatar_url: str | None = None
    card_image_url: str | None = None
    is_public: bool
    gender: str | None = None
    nsfw_allowed: bool
    total_chats_count: int
    monthly_chats_count: int
    scenarios_count: int = 0
    scenario_chats_count: int = 0
    lorebook_ids: List[UUID] = []

    class Config:
        from_attributes = True

    @classmethod
    def model_validate(cls, obj, **kwargs):
        if hasattr(obj, 'lorebooks'):
            setattr(obj, 'lorebook_ids', [lb.id for lb in obj.lorebooks])
        return super().model_validate(obj, **kwargs)


class CharacterAdminRead(CharacterRead):
    appearance: str | None = None
    personality: str | None = None
    creator_id: UUID | None = None


# Оставляем Character для обратной совместимости или как общий внутренний тип
class Character(CharacterBase):
    id: UUID
    creator_id: UUID | None = None
    total_chats_count: int
    monthly_chats_count: int
    scenarios_count: int = 0
    scenario_chats_count: int = 0

    class Config:
        from_attributes = True


# Alias for response schema
CharacterResponse = CharacterRead

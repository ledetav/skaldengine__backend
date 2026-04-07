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
    # Новые поля
    gender: str | None = None
    nsfw_allowed: bool = True


class CharacterCreate(CharacterBase):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Eldritch",
                    "description": "An ancient being of cosmic horror.",
                    "fandom": "Cthulhu Mythos",
                    "avatar_url": "https://example.com/avatar.jpg",
                    "card_image_url": "https://example.com/card.jpg",
                    "appearance": "Tentacles forming a spectral mass",
                    "personality": "Unfathomable, cold, indifferent",
                    "is_public": True
                }
            ]
        }
    }


class CharacterUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    fandom: str | None = None
    avatar_url: str | None = None
    card_image_url: str | None = None
    appearance: str | None = None
    personality: str | None = None
    is_public: bool | None = None
    gender: str | None = None
    nsfw_allowed: bool | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Eldritch (Updated)",
                    "description": "Updated description",
                    "fandom": "Updated Fandom",
                    "avatar_url": "https://example.com/avatar_new.jpg",
                    "card_image_url": "https://example.com/card_new.jpg",
                    "appearance": "More tentacles",
                    "personality": "Even more indifferent",
                    "is_public": False
                }
            ]
        }
    }


class Character(CharacterBase):
    id: UUID
    creator_id: UUID | None = None
    total_chats_count: int
    monthly_chats_count: int
    scenarios_count: int = 0
    scenario_chats_count: int = 0

    class Config:
        from_attributes = True

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class UserPersonaBase(BaseModel):
    name: str
    avatar_url: str | None = None
    age: int | None = None
    appearance: str | None = None
    personality: str | None = None
    facts: str | None = None


class UserPersonaCreate(UserPersonaBase):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Aragor",
                    "avatar_url": "https://example.com/aragor.jpg",
                    "age": 35,
                    "appearance": "Tall, dark hair, scarred face",
                    "personality": "Stoic and brave",
                    "facts": "Exiled from his homeland"
                }
            ]
        }
    }


class UserPersonaUpdate(BaseModel):
    name: str | None = None
    avatar_url: str | None = None
    age: int | None = None
    appearance: str | None = None
    personality: str | None = None
    facts: str | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Aragor the King",
                    "avatar_url": "https://example.com/aragor_king.jpg",
                    "age": 40,
                    "appearance": "Regal presence, graying hair",
                    "personality": "Wise and just",
                    "facts": "Reclaimed the throne"
                }
            ]
        }
    }


class UserPersona(UserPersonaBase):
    id: UUID
    owner_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
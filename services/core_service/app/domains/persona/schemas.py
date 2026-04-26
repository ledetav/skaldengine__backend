from pydantic import BaseModel, field_validator
from uuid import UUID
from datetime import datetime


class UserPersonaBase(BaseModel):
    name: str
    description: str | None = None
    avatar_url: str | None = None
    age: str | None = None
    appearance: str | None = None
    personality: str | None = None
    gender: str | None = None
    facts: str | None = None

    @field_validator("age", mode="before")
    @classmethod
    def age_to_str(cls, v):
        if v is None:
            return None
        return str(v)


class UserPersonaCreate(UserPersonaBase):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Aragor",
                    "description": "Exiled ranger and heir to the throne.",
                    "avatar_url": "https://example.com/aragor.jpg",
                    "age": 35,
                    "appearance": "Tall, dark hair, scarred face",
                    "personality": "Stoic and brave",
                    "gender": "male",
                    "facts": "Exiled from his homeland"
                }
            ]
        }
    }


class UserPersonaUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    avatar_url: str | None = None
    age: str | None = None
    appearance: str | None = None
    personality: str | None = None
    gender: str | None = None
    facts: str | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Aragor the King",
                    "description": "Crowned King of Gondor, leading his people to peace.",
                    "avatar_url": "https://example.com/aragor_king.jpg",
                    "age": 40,
                    "appearance": "Regal presence, graying hair",
                    "personality": "Wise and just",
                    "gender": "male",
                    "facts": "Reclaimed the throne"
                }
            ]
        }
    }


class UserPersonaResponse(UserPersonaBase):
    id: UUID
    owner_id: UUID
    lorebook_count: int = 0
    chat_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True
class UserStatistics(BaseModel):
    total_personas: int = 0
    total_lorebooks: int = 0
    total_chats: int = 0
    total_messages: int = 0

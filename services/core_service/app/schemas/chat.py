from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class ChatBase(BaseModel):
    character_id: UUID
    user_persona_id: UUID
    scenario_id: UUID | None = None
    is_acquainted: bool = False
    relationship_dynamic: str | None = None
    language: str = "ru"
    narrative_voice: str = "third"  # "first" | "second" | "third"


class ChatCreate(ChatBase):
    pass


class Chat(ChatBase):
    id: UUID
    user_id: UUID
    mode: str
    active_leaf_id: UUID | None = None
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True

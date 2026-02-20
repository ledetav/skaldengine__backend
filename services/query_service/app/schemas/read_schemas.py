from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List

class MessageRead(BaseModel):
    id: UUID
    session_id: UUID
    parent_id: Optional[UUID]
    role: str
    content: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class SessionRead(BaseModel):
    id: UUID
    user_id: UUID
    character_id: UUID
    persona_id: UUID
    scenario_id: Optional[UUID]
    mode: str
    language: str
    speech_style: str
    character_name_snapshot: str
    persona_name_snapshot: str
    relationship_context: Optional[str]
    current_step: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
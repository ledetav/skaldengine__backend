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

class CharacterRead(BaseModel):
    id: UUID
    name: str
    avatar_url: Optional[str]
    appearance: str
    personality_traits: str
    dialogue_style: str
    inner_world: Optional[str]
    behavioral_cues: Optional[str]

    class Config:
        from_attributes = True

class ScenarioRead(BaseModel):
    id: UUID
    owner_character_id: Optional[UUID]
    title: str
    description: str
    start_point: str
    end_point: str
    suggested_relationships: List[str]

    class Config:
        from_attributes = True

class UserPersonaRead(BaseModel):
    id: UUID
    owner_id: UUID
    name: str
    description: str
    avatar_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class LoreItemRead(BaseModel):
    id: UUID
    character_id: UUID
    category: str
    content: str
    keywords: Optional[str]

    class Config:
        from_attributes = True
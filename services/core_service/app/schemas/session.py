from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List

class SessionBase(BaseModel):
    character_id: UUID
    persona_id: UUID
    scenario_id: Optional[UUID] = None
    
    language: str = "ru"
    speech_style: str = "third_person"
    relationship_context: Optional[str] = None

class SessionCreate(SessionBase):
    pass 

class SessionUpdate(BaseModel):
    relationship_context: str | None = None
    current_step: int | None = None

class Session(SessionBase):
    id: UUID
    user_id: UUID
    mode: str
    character_name_snapshot: str
    persona_name_snapshot: str 
    cached_system_prompt: str
    current_step: int = 0

    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional

class BaseEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid.uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    entity_id: UUID  # ID сессии или сообщения
    event_type: str

class SessionCreatedEvent(BaseEvent):
    event_type: str = "SessionCreated"
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
    cached_system_prompt: str

class MessageAddedEvent(BaseEvent):
    event_type: str = "MessageAdded"
    session_id: UUID
    parent_id: Optional[UUID] # Для реализации ветвления
    role: str
    content: str

class MessageDeactivatedEvent(BaseEvent):
    event_type: str = "MessageDeactivated"
    session_id: UUID

class MessageEditedEvent(BaseEvent):
    event_type: str = "MessageEdited"
    session_id: UUID
    new_content: str
from pydantic import BaseModel, Field
from uuid import UUID
import uuid
from datetime import datetime, timezone
from typing import Optional

class BaseEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid.uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    entity_id: UUID  # ID сессии или сообщения
    event_type: str

class ChatCreatedEvent(BaseEvent):
    event_type: str = "ChatCreated"
    user_id: UUID
    character_id: UUID
    user_persona_id: UUID
    scenario_id: Optional[UUID]
    mode: str
    language: str
    is_acquainted: bool
    relationship_dynamic: Optional[str]
    narrative_voice: str

class MessageAddedEvent(BaseEvent):
    event_type: str = "MessageAdded"
    chat_id: UUID
    parent_id: Optional[UUID] 
    role: str
    content: str

class MessageDeactivatedEvent(BaseEvent):
    event_type: str = "MessageDeactivated"
    chat_id: UUID

class MessageEditedEvent(BaseEvent):
    event_type: str = "MessageEdited"
    chat_id: UUID
    new_content: str
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class MessageBase(BaseModel):
    role: str
    content: str

class MessageCreate(MessageBase):
    session_id: UUID
    parent_id: UUID | None = None

class MessageRegenerate(BaseModel):
    message_id: UUID

class Message(MessageBase):
    id: UUID
    session_id: UUID
    parent_id: UUID | None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

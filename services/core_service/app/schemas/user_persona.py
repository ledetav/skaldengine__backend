from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class UserPersonaBase(BaseModel):
    name: str
    description: str
    avatar_url: str | None = None

class UserPersonaCreate(UserPersonaBase):
    pass

class UserPersonaUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    avatar_url: str | None = None

class UserPersona(UserPersonaBase):
    id: UUID
    owner_id: UUID 
    created_at: datetime

    class Config:
        from_attributes = True
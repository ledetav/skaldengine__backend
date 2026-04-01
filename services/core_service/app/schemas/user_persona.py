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
    pass


class UserPersonaUpdate(BaseModel):
    name: str | None = None
    avatar_url: str | None = None
    age: int | None = None
    appearance: str | None = None
    personality: str | None = None
    facts: str | None = None


class UserPersona(UserPersonaBase):
    id: UUID
    owner_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
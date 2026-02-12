from pydantic import BaseModel
from uuid import UUID

class StyleProfileBase(BaseModel):
    name: str
    description: str | None = None
    prompt_instruction: str

class StyleProfileCreate(StyleProfileBase):
    pass

class StyleProfileUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    prompt_instruction: str | None = None

class StyleProfile(StyleProfileBase):
    id: UUID

    class Config:
        from_attributes = True

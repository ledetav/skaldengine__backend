from pydantic import BaseModel
from uuid import UUID

class LoreItemBase(BaseModel):
    category: str = "fact"
    content: str
    keywords: str | None = None

class LoreItemCreate(LoreItemBase):
    pass

class LoreItemUpdate(BaseModel):
    category: str | None = None
    content: str | None = None
    keywords: str | None = None

class LoreItem(LoreItemBase):
    id: UUID
    character_id: UUID

    class Config:
        from_attributes = True

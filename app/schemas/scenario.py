from pydantic import BaseModel
from uuid import UUID

class ScenarioBase(BaseModel):
    title: str
    description: str
    start_point: str
    end_point: str
    suggested_relationships: list[str] = []

class ScenarioCreate(ScenarioBase):
    owner_character_id: UUID | None = None

class ScenarioUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    start_point: str | None = None
    end_point: str | None = None
    suggested_relationships: list[str] | None = None

class Scenario(ScenarioBase):
    id: UUID
    owner_character_id: UUID | None

    class Config:
        from_attributes = True

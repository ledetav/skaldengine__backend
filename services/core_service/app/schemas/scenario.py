from pydantic import BaseModel
from uuid import UUID


class ScenarioBase(BaseModel):
    title: str
    description: str
    start_point: str
    end_point: str
    character_id: UUID | None = None


class ScenarioCreate(ScenarioBase):
    pass


class ScenarioUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    start_point: str | None = None
    end_point: str | None = None


class Scenario(ScenarioBase):
    id: UUID

    class Config:
        from_attributes = True

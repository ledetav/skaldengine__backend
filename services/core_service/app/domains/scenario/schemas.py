from pydantic import BaseModel
from uuid import UUID


class ScenarioBase(BaseModel):
    title: str
    location: str | None = None
    description: str
    start_point: str
    end_point: str
    character_id: UUID | None = None


class ScenarioCreate(ScenarioBase):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "The Heist",
                    "description": "Break into the vault and steal the diamond.",
                    "start_point": "Outside the bank at midnight.",
                    "end_point": "Escaping in the getaway car with the loot.",
                    "character_id": "123e4567-e89b-12d3-a456-426614174000"
                }
            ]
        }
    }


class ScenarioUpdate(BaseModel):
    title: str | None = None
    location: str | None = None
    description: str | None = None
    start_point: str | None = None
    end_point: str | None = None
    character_id: UUID | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "The Heist (Hard Mode)",
                    "description": "Break into the vault quietly.",
                    "start_point": "Rooftop infiltration.",
                    "end_point": "Stashing the loot unseen."
                }
            ]
        }
    }


class ScenarioShort(BaseModel):
    id: UUID
    character_id: UUID | None = None
    title: str
    location: str | None = None
    description: str

    class Config:
        from_attributes = True


class Scenario(ScenarioBase):
    id: UUID

    class Config:
        from_attributes = True


# Alias for response schema
ScenarioResponse = Scenario

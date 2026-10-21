from pydantic import BaseModel, Field
from uuid import UUID


class ScenarioBase(BaseModel):
    title: str = Field(..., max_length=200)
    location: str | None = Field(default=None, max_length=200)
    description: str = Field(..., max_length=500)
    start_point: str = Field(..., max_length=500)
    end_point: str = Field(..., max_length=500)
    character_id: UUID | None = None


class ScenarioCreate(ScenarioBase):
    internal_description: str | None = Field(default=None, max_length=1000)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "The Heist",
                    "description": "Break into the vault and steal the diamond.",
                    "internal_description": "The vault is actually trapped with gas. The diamond is a fake if not found by the secret lever.",
                    "start_point": "Outside the bank at midnight.",
                    "end_point": "Escaping in the getaway car with the loot.",
                    "character_id": "123e4567-e89b-12d3-a456-426614174000"
                }
            ]
        }
    }


class ScenarioUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    internal_description: str | None = Field(default=None, max_length=1000)
    start_point: str | None = Field(default=None, max_length=500)
    end_point: str | None = Field(default=None, max_length=500)
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
    chats_count: int = 0

    class Config:
        from_attributes = True


class Scenario(ScenarioBase):
    id: UUID
    chats_count: int = 0

    class Config:
        from_attributes = True


class ScenarioFull(Scenario):
    internal_description: str | None = Field(default=None, max_length=1000)


# Alias for response schema
ScenarioResponse = Scenario
ScenarioAdminResponse = ScenarioFull

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class ChatBase(BaseModel):
    character_id: UUID
    user_persona_id: UUID
    scenario_id: UUID | None = None
    title: str | None = None
    is_acquainted: bool = False
    relationship_dynamic: str | None = None
    custom_location: str | None = None
    custom_plot_hook: str | None = None
    language: str = "ru"
    narrative_voice: str = "third"  # "first" | "second" | "third"
    persona_lorebook_id: UUID | None = None
    checkpoints_count: int = 3  # Кол-во точек сценария (от 2 до 6)


class ChatCreate(ChatBase):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "character_id": "123e4567-e89b-12d3-a456-426614174000",
                    "user_persona_id": "123e4567-e89b-12d3-a456-426614174001",
                    "persona_lorebook_id": "123e4567-e89b-12d3-a456-426614174005",
                    "scenario_id": "123e4567-e89b-12d3-a456-426614174002",
                    "is_acquainted": True,
                    "relationship_dynamic": "Rivals forced to work together",
                    "language": "ru",
                    "narrative_voice": "third"
                }
            ]
        }
    }


class ChatUpdate(BaseModel):
    title: str | None = None
    language: str | None = None
    narrative_voice: str | None = None
    is_acquainted: bool | None = None
    relationship_dynamic: str | None = None
    persona_lorebook_id: UUID | None = None
    active_leaf_id: UUID | None = None


class ChatResponse(ChatBase):
    id: UUID
    user_id: UUID
    mode: str
    active_leaf_id: UUID | None = None
    created_at: datetime
    updated_at: datetime | None = None
    
    # Enriched fields for list view
    character_name: str | None = None
    user_persona_name: str | None = None
    last_message_preview: str | None = None

    class Config:
        from_attributes = True

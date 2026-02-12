from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class SessionBase(BaseModel):
    mode: str = "sandbox"
    relationship_context: str

class SessionCreate(SessionBase):
    ai_character_id: UUID
    scenario_id: UUID | None = None
    style_profile_id: UUID | None = None
    user_name_snapshot: str
    user_desc_snapshot: str

class SessionUpdate(BaseModel):
    relationship_context: str | None = None
    plot_points: list[str] | None = None
    current_plot_index: int | None = None

class Session(SessionBase):
    id: UUID
    user_id: UUID
    ai_character_id: UUID
    scenario_id: UUID | None
    style_profile_id: UUID | None
    user_name_snapshot: str
    user_desc_snapshot: str
    plot_points: list[str] | None
    current_plot_index: int
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True

from pydantic import BaseModel
from uuid import UUID


class ChatCheckpointBase(BaseModel):
    order_num: int
    goal_description: str
    is_completed: bool = False


class ChatCheckpointCreate(ChatCheckpointBase):
    pass


class ChatCheckpointUpdate(BaseModel):
    is_completed: bool | None = None
    goal_description: str | None = None


class ChatCheckpoint(ChatCheckpointBase):
    id: UUID
    chat_id: UUID

    class Config:
        from_attributes = True

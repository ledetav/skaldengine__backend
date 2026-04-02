from pydantic import BaseModel
from uuid import UUID


class ChatCheckpointBase(BaseModel):
    order_num: int
    goal_description: str
    is_completed: bool = False


class ChatCheckpointCreate(ChatCheckpointBase):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "order_num": 1,
                    "goal_description": "User must figure out the code to the vault.",
                    "is_completed": False
                }
            ]
        }
    }


class ChatCheckpointUpdate(BaseModel):
    is_completed: bool | None = None
    goal_description: str | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "order_num": 2,
                    "goal_description": "User has figured out the code.",
                    "is_completed": True
                }
            ]
        }
    }


class ChatCheckpoint(ChatCheckpointBase):
    id: UUID
    chat_id: UUID

    class Config:
        from_attributes = True

from pydantic import BaseModel

class UserStatistics(BaseModel):
    total_chats: int
    total_personas: int
    total_lorebooks: int

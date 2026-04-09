from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from shared.base.repository import BaseRepository
from .message_models import Message

class MessageRepository(BaseRepository[Message]):
    def __init__(self, db):
        super().__init__(Message, db)

    async def get_chat_history(self, chat_id: UUID) -> List[Message]:
        query = select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at.asc())
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_parent(self, parent_id: UUID) -> List[Message]:
        query = select(Message).where(Message.parent_id == parent_id)
        result = await self.db.execute(query)
        return result.scalars().all()

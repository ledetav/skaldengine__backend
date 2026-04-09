from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from app.repositories.base_repository import BaseRepository
from app.models.chat import Chat

class ChatRepository(BaseRepository[Chat]):
    def __init__(self, db):
        super().__init__(Chat, db)

    async def get_by_user(self, user_id: UUID, skip: int = 0, limit: int = 20) -> List[Chat]:
        query = select(Chat).where(Chat.user_id == user_id).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_with_relations(self, chat_id: UUID) -> Optional[Chat]:
        # Optimization: we can use selectinload or joinedload here if needed
        # For now, let's keep it simple as SQLAlchemy models have relationships defined
        return await self.get(chat_id)

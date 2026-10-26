"""
Репозиторий для доступа к данным ролевых сессий (Chat).
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from shared.base.repository import BaseRepository
from .models import Chat


class ChatRepository(BaseRepository[Chat]):
    """
    Репозиторий игровых сессий пользователей.
    """
    def __init__(self, db):
        super().__init__(Chat, db)

    async def get_by_user(self, user_id: UUID, skip: int = 0, limit: int = 20) -> List[Chat]:
        """Получить список чатов пользователя с пагинацией."""
        query = select(Chat).where(Chat.user_id == user_id).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_with_relations(self, chat_id: UUID) -> Optional[Chat]:
        """Получить чат со связанными сущностями."""
        return await self.get(chat_id)


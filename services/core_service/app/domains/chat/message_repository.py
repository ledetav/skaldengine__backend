"""
Репозиторий для доступа к сообщениям ролевого диалога (Message).
"""

from typing import List
from uuid import UUID
from sqlalchemy import select
from shared.base.repository import BaseRepository
from .message_models import Message


class MessageRepository(BaseRepository[Message]):
    """
    Репозиторий сообщений диалога с поддержкой сортировки по времени.
    """
    def __init__(self, db):
        super().__init__(Message, db)

    async def get_chat_history(self, chat_id: UUID) -> List[Message]:
        """Получить все сообщения чата в хронологическом порядке."""
        query = select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at.asc())
        result = await self.db.execute(query)
        return list(result.scalars().all())


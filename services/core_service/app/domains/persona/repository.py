"""
Репозиторий для работы с персонами пользователей (UserPersona).
"""

from typing import List
from uuid import UUID
from sqlalchemy import select, func
from shared.base.repository import BaseRepository
from .models import UserPersona


class UserPersonaRepository(BaseRepository[UserPersona]):
    """
    Репозиторий сущности UserPersona с поддержкой подсчета связанных сущностей
    (лорбуки, чаты) и агрегированной статистики.
    """
    def __init__(self, db):
        super().__init__(UserPersona, db)

    async def get_by_owner(self, owner_id: UUID) -> List[UserPersona]:
        """
        Получение всех персон указанного владельца вместе с количеством
        привязанных лорбуков и активных чатов (с защитой от N+1 запросов).
        """
        from app.domains.chat.models import Chat
        from app.domains.lorebook.models import Lorebook

        # Скалярные подзапросы для предотвращения проблемы N+1
        lb_subq = (
            select(func.count(Lorebook.id))
            .where(Lorebook.user_persona_id == UserPersona.id)
            .scalar_subquery()
            .correlate(UserPersona)
        )

        chat_subq = (
            select(func.count(Chat.id))
            .where(Chat.user_persona_id == UserPersona.id)
            .scalar_subquery()
            .correlate(UserPersona)
        )

        # Единый запрос для получения персон и их счетчиков
        query = (
            select(UserPersona, lb_subq.label("lorebook_count"), chat_subq.label("chat_count"))
            .where(UserPersona.owner_id == owner_id)
        )

        result = await self.db.execute(query)
        rows = result.all()

        # Восстановление объектов персон с установленными счетчиками
        personas = []
        for persona, lb_count, chat_count in rows:
            persona.lorebook_count = lb_count or 0
            persona.chat_count = chat_count or 0
            personas.append(persona)

        return personas

    async def get_aggregate_stats(self, owner_id: UUID) -> dict:
        """
        Получение агрегированных статистических показателей пользователя:
        общее число персон, лорбуков, чатов и сообщений.
        """
        from app.domains.chat.models import Chat
        from app.domains.lorebook.models import Lorebook
        from app.domains.chat.message_models import Message

        query = select(
            func.count(UserPersona.id).label("total_personas"),
            func.coalesce(func.sum(
                select(func.count(Lorebook.id))
                .where(Lorebook.user_persona_id == UserPersona.id)
                .scalar_subquery()
            ), 0).label("total_lorebooks"),
            func.coalesce(func.sum(
                select(func.count(Chat.id))
                .where(Chat.user_persona_id == UserPersona.id)
                .scalar_subquery()
            ), 0).label("total_chats"),
            func.coalesce(func.sum(
                select(func.count(Message.id))
                .join(Chat, Chat.id == Message.chat_id)
                .where(Chat.user_persona_id == UserPersona.id)
                .scalar_subquery()
            ), 0).label("total_messages")
        ).where(UserPersona.owner_id == owner_id)

        result = await self.db.execute(query)
        row = result.first()

        return {
            "total_personas": row.total_personas if row else 0,
            "total_lorebooks": row.total_lorebooks if row else 0,
            "total_chats": row.total_chats if row else 0,
            "total_messages": row.total_messages if row else 0
        }

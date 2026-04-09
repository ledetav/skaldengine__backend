from typing import List
from uuid import UUID
from sqlalchemy import select, func
from app.repositories.base_repository import BaseRepository
from app.models.user_persona import UserPersona

class UserPersonaRepository(BaseRepository[UserPersona]):
    def __init__(self, db):
        super().__init__(UserPersona, db)

    async def get_by_owner(self, owner_id: UUID) -> List[UserPersona]:
        from app.models.chat import Chat
        from app.models.lorebook import Lorebook

        # Common query with counts
        query = select(UserPersona).where(UserPersona.owner_id == owner_id)
        result = await self.db.execute(query)
        personas = result.scalars().all()

        for persona in personas:
            # Count lorebooks
            lb_query = select(func.count(Lorebook.id)).where(Lorebook.user_persona_id == persona.id)
            lb_count = await self.db.execute(lb_query)
            persona.lorebook_count = lb_count.scalar() or 0

            # Count chats
            chat_query = select(func.count(Chat.id)).where(Chat.user_persona_id == persona.id)
            chat_count = await self.db.execute(chat_query)
            persona.chat_count = chat_count.scalar() or 0

        return personas

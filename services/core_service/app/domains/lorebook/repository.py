from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from shared.base.repository import BaseRepository
from .models import Lorebook, LorebookEntry

class LorebookRepository(BaseRepository[Lorebook]):
    def __init__(self, db):
        super().__init__(Lorebook, db)

    async def get_by_character(self, character_id: UUID) -> List[Lorebook]:
        query = select(Lorebook).where(Lorebook.character_id == character_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_persona(self, persona_id: UUID) -> List[Lorebook]:
        query = select(Lorebook).where(Lorebook.user_persona_id == persona_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_user(self, user_id: UUID) -> List[Lorebook]:
        from app.domains.character.models import Character
        from app.domains.persona.models import UserPersona
        from sqlalchemy import or_
        query = select(Lorebook).join(Character, Lorebook.character_id == Character.id, isouter=True)\
            .join(UserPersona, Lorebook.user_persona_id == UserPersona.id, isouter=True)\
            .where(or_(Character.creator_id == user_id, UserPersona.owner_id == user_id))
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_fandom_lorebook(self, fandom_name: str) -> Optional[Lorebook]:
        query = select(Lorebook).where(
            Lorebook.fandom == fandom_name,
            Lorebook.character_id == None,
            Lorebook.user_persona_id == None
        )
        result = await self.db.execute(query)
        return result.scalars().first()

class LorebookEntryRepository(BaseRepository[LorebookEntry]):
    def __init__(self, db):
        super().__init__(LorebookEntry, db)

    async def get_by_lorebook(self, lorebook_id: UUID) -> List[LorebookEntry]:
        query = select(LorebookEntry).where(LorebookEntry.lorebook_id == lorebook_id)
        result = await self.db.execute(query)
        return result.scalars().all()

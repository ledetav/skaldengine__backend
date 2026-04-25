from typing import List, Optional, Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from shared.base.repository import BaseRepository
from .models import Lorebook, LorebookEntry

class LorebookRepository(BaseRepository[Lorebook]):
    def __init__(self, db):
        super().__init__(Lorebook, db)

    async def get(self, id: Any) -> Optional[Lorebook]:
        query = select(self.model).options(selectinload(Lorebook.entries)).where(self.model.id == id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_character(self, character_id: UUID) -> List[Lorebook]:
        query = select(Lorebook).options(selectinload(Lorebook.entries)).where(Lorebook.character_id == character_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_persona(self, persona_id: UUID) -> List[Lorebook]:
        query = select(Lorebook).options(selectinload(Lorebook.entries)).where(Lorebook.user_persona_id == persona_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_user(self, user_id: UUID) -> List[Lorebook]:
        from app.domains.character.models import Character
        from app.domains.persona.models import UserPersona
        from sqlalchemy import or_
        query = select(Lorebook).options(selectinload(Lorebook.entries))\
            .join(Character, Lorebook.character_id == Character.id, isouter=True)\
            .join(UserPersona, Lorebook.user_persona_id == UserPersona.id, isouter=True)\
            .where(or_(Character.creator_id == user_id, UserPersona.owner_id == user_id))
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[Lorebook]:
        query = select(Lorebook).options(selectinload(Lorebook.entries)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_multi_with_count(self, skip: int = 0, limit: int = 20, lb_type: Optional[str] = None) -> tuple[List[Lorebook], int]:
        from sqlalchemy import func
        query = select(Lorebook).options(selectinload(Lorebook.entries))
        if lb_type:
            query = query.where(Lorebook.type == lb_type)
        
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().all()

        count_query = select(func.count()).select_from(Lorebook)
        if lb_type:
            count_query = count_query.where(Lorebook.type == lb_type)
            
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        return list(items), total

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

    async def get_by_lorebook_with_count(self, lorebook_id: UUID, skip: int = 0, limit: int = 20) -> tuple[List[LorebookEntry], int]:
        from sqlalchemy import func
        query = select(LorebookEntry).where(LorebookEntry.lorebook_id == lorebook_id).offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().all()

        count_query = select(func.count()).select_from(LorebookEntry).where(LorebookEntry.lorebook_id == lorebook_id)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        return list(items), total

    async def create_bulk(self, lorebook_id: UUID, entries_data: List[dict]) -> List[LorebookEntry]:
        entries = [
            LorebookEntry(lorebook_id=lorebook_id, **data)
            for data in entries_data
        ]
        self.db.add_all(entries)
        await self.db.commit()
        for entry in entries:
            await self.db.refresh(entry)
        return entries

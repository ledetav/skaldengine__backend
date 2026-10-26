"""
Репозитории для работы со справочниками мира (Lorebook) и их записями (LorebookEntry).
"""

from typing import List, Optional, Any
from uuid import UUID
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import selectinload
from shared.base.repository import BaseRepository
from .models import Lorebook, LorebookEntry


class LorebookRepository(BaseRepository[Lorebook]):
    """
    Репозиторий сущности Lorebook: выборка по персонажу, персоне, пользователю
    и получение глобальных фандомных справочников.
    """
    def __init__(self, db):
        super().__init__(Lorebook, db)

    async def get(self, id: Any) -> Optional[Lorebook]:
        """Получить лорбук по ID с предзагрузкой всех записей."""
        query = select(self.model).options(selectinload(Lorebook.entries)).where(self.model.id == id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_character(self, character_id: UUID) -> List[Lorebook]:
        """Получить лорбуки, связанные с конкретным персонажем."""
        query = select(Lorebook).options(selectinload(Lorebook.entries)).where(Lorebook.character_id == character_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_persona(self, persona_id: UUID) -> List[Lorebook]:
        """Получить лорбуки, связанные с персоной игрока."""
        query = select(Lorebook).options(selectinload(Lorebook.entries)).where(Lorebook.user_persona_id == persona_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_user(self, user_id: UUID) -> List[Lorebook]:
        """Получить все лорбуки, принадлежащие пользователю (через созданных персонажей или персоны)."""
        from app.domains.character.models import Character
        from app.domains.persona.models import UserPersona
        query = select(Lorebook).options(selectinload(Lorebook.entries))\
            .join(Character, Lorebook.character_id == Character.id, isouter=True)\
            .join(UserPersona, Lorebook.user_persona_id == UserPersona.id, isouter=True)\
            .where(or_(Character.creator_id == user_id, UserPersona.owner_id == user_id))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[Lorebook]:
        """Получить список лорбуков с предзагрузкой записей."""
        query = select(Lorebook).options(selectinload(Lorebook.entries)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_multi_with_count(self, skip: int = 0, limit: int = 20, lb_type: Optional[str] = None) -> tuple[List[Lorebook], int]:
        """Получить пагинированный список лорбуков с общим количеством элементов и фильтром по типу."""
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
        """Получить базовый глобальный лорбук фандома (не привязанный к конкретному боту/персоне)."""
        query = select(Lorebook).where(
            Lorebook.fandom == fandom_name,
            Lorebook.character_id == None,
            Lorebook.user_persona_id == None
        )
        result = await self.db.execute(query)
        return result.scalars().first()


class LorebookEntryRepository(BaseRepository[LorebookEntry]):
    """
    Репозиторий записей справочника (LorebookEntry).
    """
    def __init__(self, db):
        super().__init__(LorebookEntry, db)

    async def get_by_lorebook(self, lorebook_id: UUID) -> List[LorebookEntry]:
        """Получить все записи конкретного лорбука."""
        query = select(LorebookEntry).where(LorebookEntry.lorebook_id == lorebook_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_lorebook_with_count(self, lorebook_id: UUID, skip: int = 0, limit: int = 20, sort_by: str = "created_at") -> tuple[List[LorebookEntry], int]:
        """Получить пагинированный список записей лорбука с сортировкой по приоритету или дате."""
        query = select(LorebookEntry).where(LorebookEntry.lorebook_id == lorebook_id)
        
        if sort_by == "priority":
            query = query.order_by(desc(LorebookEntry.priority), desc(LorebookEntry.created_at))
        else:
            query = query.order_by(desc(LorebookEntry.created_at))
            
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().all()

        count_query = select(func.count()).select_from(LorebookEntry).where(LorebookEntry.lorebook_id == lorebook_id)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        return list(items), total

    async def create_bulk(self, lorebook_id: UUID, entries_data: List[dict]) -> List[LorebookEntry]:
        """Пакетное создание нескольких записей лорбука в одной транзакции."""
        entries = [
            LorebookEntry(lorebook_id=lorebook_id, **data)
            for data in entries_data
        ]
        self.db.add_all(entries)
        await self.db.commit()
        for entry in entries:
            await self.db.refresh(entry)
        return entries


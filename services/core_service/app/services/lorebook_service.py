from typing import List, Optional
from uuid import UUID
from app.services.base_service import BaseService
from app.repositories.lorebook_repository import LorebookRepository, LorebookEntryRepository
from app.models.lorebook import Lorebook, LorebookEntry
from app.schemas.lorebook import LorebookCreate, LorebookUpdate, LorebookEntryCreate, LorebookEntryUpdate

class LorebookService(BaseService[LorebookRepository]):
    def __init__(self, repository: LorebookRepository, entry_repository: LorebookEntryRepository):
        super().__init__(repository)
        self.entry_repository = entry_repository

    async def get_lorebooks(self, character_id: Optional[UUID] = None, persona_id: Optional[UUID] = None) -> List[Lorebook]:
        if character_id:
            return await self.repository.get_by_character(character_id)
        if persona_id:
            return await self.repository.get_by_persona(persona_id)
        return await self.repository.get_multi()

    async def create_lorebook(self, lorebook_in: LorebookCreate) -> Lorebook:
        return await self.repository.create(obj_in=lorebook_in)

    async def get_lorebook(self, lorebook_id: UUID) -> Optional[Lorebook]:
        return await self.repository.get(lorebook_id)

    async def get_fandom_lorebook(self, fandom_name: str) -> Optional[Lorebook]:
        return await self.repository.get_fandom_lorebook(fandom_name)

    async def update_lorebook(self, lorebook_id: UUID, lorebook_update: LorebookUpdate) -> Optional[Lorebook]:
        lorebook = await self.repository.get(lorebook_id)
        if not lorebook:
            return None
        return await self.repository.update(db_obj=lorebook, obj_in=lorebook_update)

    async def delete_lorebook(self, lorebook_id: UUID) -> bool:
        lorebook = await self.repository.get(lorebook_id)
        if not lorebook:
            return False
        await self.repository.delete(id=lorebook_id)
        return True

    # Entry methods
    async def create_entry(self, lorebook_id: UUID, entry_in: LorebookEntryCreate) -> LorebookEntry:
        entry_data = entry_in.model_dump()
        entry_data["lorebook_id"] = lorebook_id
        return await self.entry_repository.create(obj_in=entry_data)

    async def update_entry(self, entry_id: UUID, entry_update: LorebookEntryUpdate) -> Optional[LorebookEntry]:
        entry = await self.entry_repository.get(entry_id)
        if not entry:
            return None
        return await self.entry_repository.update(db_obj=entry, obj_in=entry_update)

    async def delete_entry(self, entry_id: UUID) -> bool:
        entry = await self.entry_repository.get(entry_id)
        if not entry:
            return False
        await self.entry_repository.delete(id=entry_id)
        return True

from typing import List, Optional
from uuid import UUID
from shared.base.service import BaseService
from app.domains.lorebook.repository import LorebookRepository, LorebookEntryRepository
from app.domains.lorebook.models import Lorebook, LorebookEntry
from app.domains.lorebook.schemas import LorebookCreate, LorebookUpdate, LorebookEntryCreate, LorebookEntryUpdate
from app.core.broadcast import manager

class LorebookService(BaseService[LorebookRepository]):
    def __init__(self, repository: LorebookRepository, entry_repository: LorebookEntryRepository):
        super().__init__(repository)
        self.entry_repository = entry_repository

    async def get_lorebooks(self, 
        character_id: Optional[UUID] = None, 
        persona_id: Optional[UUID] = None, 
        user_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[Lorebook], int] | List[Lorebook]:
        if character_id:
            return await self.repository.get_by_character(character_id)
        if persona_id:
            return await self.repository.get_by_persona(persona_id)
        if user_id:
            return await self.repository.get_by_user(user_id)
        return await self.repository.get_multi_with_count(skip=skip, limit=limit)

    async def create_lorebook(self, lorebook_in: LorebookCreate) -> Lorebook:
        from fastapi import HTTPException
        from app.domains.lorebook.models import LorebookType

        if lorebook_in.type == LorebookType.FANDOM:
            if not lorebook_in.fandom:
                raise HTTPException(status_code=400, detail="Fandom lorebook must have a fandom name")
            if lorebook_in.fandom.lower() == "original":
                raise HTTPException(status_code=400, detail="Fandom name 'original' is reserved for character lorebooks")
        elif lorebook_in.type == LorebookType.CHARACTER:
            if not lorebook_in.character_id:
                raise HTTPException(status_code=400, detail="Character lorebook must be linked to a character")
        elif lorebook_in.type == LorebookType.PERSONA:
            if not lorebook_in.user_persona_id:
                raise HTTPException(status_code=400, detail="Persona lorebook must be linked to a user persona")

        created = await self.repository.create(obj_in=lorebook_in)
        
        # Broadcast creation
        await manager.broadcast({
            "type": "NEW_LOREBOOK",
            "data": {
                "id": str(created.id),
                "name": created.name,
                "type": created.type,
                "fandom": created.fandom,
                "character_id": str(created.character_id) if created.character_id else None,
                "user_persona_id": str(created.user_persona_id) if created.user_persona_id else None,
                "entries_count": 0,
                "tags": created.tags or []
            }
        })
        return created

    async def get_lorebook(self, lorebook_id: UUID) -> Optional[Lorebook]:
        return await self.repository.get(lorebook_id)

    async def get_fandom_lorebook(self, fandom_name: str) -> Optional[Lorebook]:
        return await self.repository.get_fandom_lorebook(fandom_name)

    async def update_lorebook(self, lorebook_id: UUID, lorebook_update: LorebookUpdate) -> Optional[Lorebook]:
        lorebook = await self.repository.get(lorebook_id)
        if not lorebook:
            return None
        updated = await self.repository.update(db_obj=lorebook, obj_in=lorebook_update)
        
        # Broadcast update
        await manager.broadcast({
            "type": "UPDATE_LOREBOOK",
            "data": {
                "id": str(updated.id),
                "name": updated.name,
                "type": updated.type,
                "fandom": updated.fandom,
                "character_id": str(updated.character_id) if updated.character_id else None,
                "user_persona_id": str(updated.user_persona_id) if updated.user_persona_id else None,
                "tags": updated.tags or []
            }
        })
        return updated

    async def delete_lorebook(self, lorebook_id: UUID) -> bool:
        lorebook = await self.repository.get(lorebook_id)
        if not lorebook:
            return False
        await self.repository.delete(id=lorebook_id)
        
        # Broadcast deletion
        await manager.broadcast({
            "type": "DELETE_LOREBOOK",
            "data": {"id": str(lorebook_id)}
        })
        return True

    # Entry methods
    async def create_entry(self, lorebook_id: UUID, entry_in: LorebookEntryCreate) -> LorebookEntry:
        entry_data = entry_in.model_dump()
        entry_data["lorebook_id"] = lorebook_id
        created = await self.entry_repository.create(obj_in=entry_data)
        
        # Broadcast entry update (refresh needed for this lorebook)
        await manager.broadcast({
            "type": "REFRESH_LOREBOOK_ENTRIES",
            "data": {"lorebook_id": str(lorebook_id)}
        })
        return created

    async def create_entries_bulk(self, lorebook_id: UUID, entries_in: List[LorebookEntryCreate]) -> List[LorebookEntry]:
        entries_data = [e.model_dump() for e in entries_in]
        created_entries = await self.entry_repository.create_bulk(lorebook_id, entries_data)
        
        # Broadcast entry update
        await manager.broadcast({
            "type": "REFRESH_LOREBOOK_ENTRIES",
            "data": {"lorebook_id": str(lorebook_id)}
        })
        return created_entries

    async def update_entry(self, entry_id: UUID, entry_update: LorebookEntryUpdate) -> Optional[LorebookEntry]:
        entry = await self.entry_repository.get(entry_id)
        if not entry:
            return None
        updated = await self.entry_repository.update(db_obj=entry, obj_in=entry_update)
        
        if updated:
            await manager.broadcast({
                "type": "REFRESH_LOREBOOK_ENTRIES",
                "data": {"lorebook_id": str(updated.lorebook_id)}
            })
        return updated

    async def get_entry(self, entry_id: UUID) -> Optional[LorebookEntry]:
        return await self.entry_repository.get(entry_id)

    async def delete_entry(self, entry_id: UUID) -> bool:
        entry = await self.entry_repository.get(entry_id)
        if not entry:
            return False
        lorebook_id = entry.lorebook_id
        await self.entry_repository.delete(id=entry_id)
        
        # Broadcast entry update
        await manager.broadcast({
            "type": "REFRESH_LOREBOOK_ENTRIES",
            "data": {"lorebook_id": str(lorebook_id)}
        })
        return True

    async def get_entries_by_lorebook(self, lorebook_id: UUID, skip: int = 0, limit: int = 20) -> tuple[List[LorebookEntry], int]:
        return await self.entry_repository.get_by_lorebook_with_count(lorebook_id, skip=skip, limit=limit)

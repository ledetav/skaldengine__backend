from typing import List, Optional
from uuid import UUID
from fastapi import status
from shared.base.controller import BaseController
from .service import LorebookService
from .schemas import LorebookCreate, LorebookUpdate, LorebookEntryCreate, LorebookEntryUpdate, LorebookEntryBulkCreate, Lorebook as LorebookSchema, LorebookEntry as LorebookEntrySchema
from shared.schemas.response import BaseResponse

class LorebookController(BaseController):
    def __init__(self, lorebook_service: LorebookService):
        self.lorebook_service = lorebook_service

    async def get_lorebooks(self, 
        character_id: Optional[UUID] = None, 
        persona_id: Optional[UUID] = None, 
        user_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 20
    ) -> BaseResponse:
        lorebooks = await self.lorebook_service.get_lorebooks(character_id, persona_id, user_id, skip=skip, limit=limit)
        data = [LorebookSchema.model_validate(lb) for lb in lorebooks]
        return self.handle_success(data=data)

    async def check_fandom(self, fandom_name: str) -> BaseResponse:
        lorebook = await self.lorebook_service.get_fandom_lorebook(fandom_name)
        return self.handle_success(data={"exists": lorebook is not None})

    async def create_lorebook(self, lorebook_in: LorebookCreate, is_admin: bool = False) -> BaseResponse:
        if not is_admin and not lorebook_in.character_id:
            self.handle_error(
                "Moderators can only create character-specific lorebooks (character_id is required)", 
                status_code=status.HTTP_400_BAD_REQUEST
            )
        lorebook = await self.lorebook_service.create_lorebook(lorebook_in)
        return self.handle_success(data=LorebookSchema.model_validate(lorebook))

    async def get_lorebook(self, lorebook_id: UUID) -> BaseResponse:
        lorebook = await self.lorebook_service.get_lorebook(lorebook_id)
        if not lorebook:
            self.handle_error("Lorebook not found", status_code=status.HTTP_404_NOT_FOUND)
        
        data = LorebookSchema.model_validate(lorebook)
        return self.handle_success(data=data)

    async def update_lorebook(self, lorebook_id: UUID, lorebook_update: LorebookUpdate, is_admin: bool = False) -> BaseResponse:
        lorebook = await self.lorebook_service.get_lorebook(lorebook_id)
        if not lorebook:
            self.handle_error("Lorebook not found", status_code=status.HTTP_404_NOT_FOUND)
        
        if not is_admin and not lorebook.character_id:
            self.handle_error("Moderators cannot edit fandom-wide lorebooks", status_code=status.HTTP_403_FORBIDDEN)
            
        updated = await self.lorebook_service.update_lorebook(lorebook_id, lorebook_update)
        return self.handle_success(data=updated)

    async def delete_lorebook(self, lorebook_id: UUID, is_admin: bool = False) -> BaseResponse:
        lorebook = await self.lorebook_service.get_lorebook(lorebook_id)
        if not lorebook:
            self.handle_error("Lorebook not found", status_code=status.HTTP_404_NOT_FOUND)
            
        if not is_admin and not lorebook.character_id:
            self.handle_error("Moderators cannot delete fandom-wide lorebooks", status_code=status.HTTP_403_FORBIDDEN)
            
        await self.lorebook_service.delete_lorebook(lorebook_id)
        return self.handle_success(data=None)

    # Entry methods
    async def create_entry(self, lorebook_id: UUID, entry_in: LorebookEntryCreate) -> BaseResponse:
        entry = await self.lorebook_service.create_entry(lorebook_id, entry_in)
        return self.handle_success(data=LorebookEntrySchema.model_validate(entry))

    async def create_entries_bulk(self, lorebook_id: UUID, bulk_in: LorebookEntryBulkCreate) -> BaseResponse:
        entries = await self.lorebook_service.create_entries_bulk(lorebook_id, bulk_in.entries)
        data = [LorebookEntrySchema.model_validate(e) for e in entries]
        return self.handle_success(data=data)

    async def get_entry(self, entry_id: UUID) -> BaseResponse:
        entry = await self.lorebook_service.get_entry(entry_id)
        if not entry:
            self.handle_error("Entry not found", status_code=status.HTTP_404_NOT_FOUND)
        return self.handle_success(data=LorebookEntrySchema.model_validate(entry))

    async def update_entry(self, entry_id: UUID, entry_update: LorebookEntryUpdate) -> BaseResponse:
        entry = await self.lorebook_service.update_entry(entry_id, entry_update)
        if not entry:
            self.handle_error("Entry not found", status_code=status.HTTP_404_NOT_FOUND)
        return self.handle_success(data=LorebookEntrySchema.model_validate(entry))

    async def delete_entry(self, entry_id: UUID) -> BaseResponse:
        success = await self.lorebook_service.delete_entry(entry_id)
        if not success:
            self.handle_error("Entry not found", status_code=status.HTTP_404_NOT_FOUND)
        return self.handle_success(data=None)

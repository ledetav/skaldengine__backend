from typing import List, Optional
from uuid import UUID
from fastapi import status
from app.api.base_controller import BaseController
from app.services.character_attribute_service import CharacterAttributeService
from app.schemas.character_attribute import CharacterAttributeCreate, CharacterAttributeUpdate, CharacterAttributeBulkCreate
from app.schemas.response import BaseResponse

class CharacterAttributeController(BaseController):
    def __init__(self, attribute_service: CharacterAttributeService):
        self.attribute_service = attribute_service

    async def get_attributes(self, character_id: Optional[UUID] = None, category: Optional[str] = None) -> BaseResponse:
        attributes = await self.attribute_service.get_attributes(character_id, category)
        return self.handle_success(data=attributes)

    async def create_attribute(self, attribute_in: CharacterAttributeCreate) -> BaseResponse:
        attribute = await self.attribute_service.create_attribute(attribute_in)
        return self.handle_success(data=attribute, status_code=status.HTTP_201_CREATED)

    async def create_bulk(self, bulk_in: CharacterAttributeBulkCreate) -> BaseResponse:
        attributes = await self.attribute_service.create_bulk(bulk_in)
        return self.handle_success(data=attributes, status_code=status.HTTP_201_CREATED)

    async def update_attribute(self, attribute_id: UUID, attribute_update: CharacterAttributeUpdate) -> BaseResponse:
        attribute = await self.attribute_service.update_attribute(attribute_id, attribute_update)
        if not attribute:
            self.handle_error("Attribute not found", status_code=status.HTTP_404_NOT_FOUND)
        return self.handle_success(data=attribute)

    async def delete_attribute(self, attribute_id: UUID) -> BaseResponse:
        success = await self.attribute_service.delete_attribute(attribute_id)
        if not success:
            self.handle_error("Attribute not found", status_code=status.HTTP_404_NOT_FOUND)
        return self.handle_success(data=None)

    async def delete_for_character(self, character_id: UUID) -> BaseResponse:
        await self.attribute_service.delete_for_character(character_id)
        return self.handle_success(data=None)

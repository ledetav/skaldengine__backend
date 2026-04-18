from typing import List, Optional
from uuid import UUID
from app.services.base_service import BaseService
from app.repositories.character_attribute_repository import CharacterAttributeRepository
from app.models.character_attribute import CharacterAttribute
from app.schemas.character_attribute import CharacterAttributeCreate, CharacterAttributeUpdate, CharacterAttributeBulkCreate

class CharacterAttributeService(BaseService[CharacterAttributeRepository]):
    async def get_attributes(self, character_id: Optional[UUID] = None, category: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[CharacterAttribute]:
        if character_id:
            return await self.repository.get_by_character(character_id, category)
        return await self.repository.get_multi(skip=skip, limit=limit)

    async def get_attribute(self, attribute_id: UUID) -> Optional[CharacterAttribute]:
        return await self.repository.get(attribute_id)

    async def create_attribute(self, attribute_in: CharacterAttributeCreate) -> CharacterAttribute:
        return await self.repository.create(obj_in=attribute_in)

    async def create_bulk(self, bulk_in: CharacterAttributeBulkCreate) -> List[CharacterAttribute]:
        new_attrs = []
        for attr_base in bulk_in.attributes:
            attr_data = attr_base.model_dump()
            attr_data["character_id"] = bulk_in.character_id
            db_obj = await self.repository.create(obj_in=attr_data)
            new_attrs.append(db_obj)
        return new_attrs

    async def update_attribute(self, attribute_id: UUID, attribute_update: CharacterAttributeUpdate) -> Optional[CharacterAttribute]:
        attribute = await self.repository.get(attribute_id)
        if not attribute:
            return None
        return await self.repository.update(db_obj=attribute, obj_in=attribute_update)

    async def delete_attribute(self, attribute_id: UUID) -> bool:
        attribute = await self.repository.get(attribute_id)
        if not attribute:
            return False
        await self.repository.delete(id=attribute_id)
        return True

    async def delete_for_character(self, character_id: UUID):
        await self.repository.delete_by_character(character_id)

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, delete
from app.repositories.base_repository import BaseRepository
from app.models.character_attribute import CharacterAttribute

class CharacterAttributeRepository(BaseRepository[CharacterAttribute]):
    def __init__(self, db):
        super().__init__(CharacterAttribute, db)

    async def get_by_character(self, character_id: UUID, category: Optional[str] = None) -> List[CharacterAttribute]:
        query = select(CharacterAttribute).where(CharacterAttribute.character_id == character_id)
        if category:
            query = query.where(CharacterAttribute.category == category)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def delete_by_character(self, character_id: UUID):
        query = delete(CharacterAttribute).where(CharacterAttribute.character_id == character_id)
        await self.db.execute(query)
        await self.db.commit()

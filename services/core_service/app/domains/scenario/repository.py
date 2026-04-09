from typing import List
from uuid import UUID
from sqlalchemy import select
from shared.base.repository import BaseRepository
from .models import Scenario

class ScenarioRepository(BaseRepository[Scenario]):
    def __init__(self, db):
        super().__init__(Scenario, db)

    async def get_by_character(self, character_id: UUID) -> List[Scenario]:
        query = select(Scenario).where(Scenario.character_id == character_id)
        result = await self.db.execute(query)
        return result.scalars().all()

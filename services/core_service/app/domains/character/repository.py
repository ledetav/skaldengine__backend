from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, func
from shared.base.repository import BaseRepository
from .models import Character
from app.models.scenario import Scenario
from app.models.chat import Chat

class CharacterRepository(BaseRepository[Character]):
    def __init__(self, db):
        super().__init__(Character, db)

    async def get_active_characters(self, skip: int = 0, limit: int = 20) -> List[Character]:
        query = select(Character).where(
            Character.is_deleted == False,
            Character.is_public == True
        ).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_scenarios_count(self, character_id: UUID) -> int:
        query = select(func.count()).select_from(Scenario).where(Scenario.character_id == character_id)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_scenario_chats_count(self, character_id: UUID) -> int:
        query = select(func.count()).select_from(Chat).where(
            Chat.character_id == character_id,
            Chat.mode == "scenario"
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

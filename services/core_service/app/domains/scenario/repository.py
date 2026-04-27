from typing import List, Tuple
from uuid import UUID
from sqlalchemy import select, func
from shared.base.repository import BaseRepository
from .models import Scenario
from app.domains.chat.models import Chat

class ScenarioRepository(BaseRepository[Scenario]):
    def __init__(self, db):
        super().__init__(Scenario, db)

    async def get_multi_with_counts(self, skip: int = 0, limit: int = 100) -> List[Scenario]:
        chat_count_subquery = (
            select(func.count(Chat.id))
            .where(Chat.scenario_id == Scenario.id)
            .correlate(Scenario)
            .label("chats_count")
        )
        
        query = select(Scenario, chat_count_subquery).offset(skip).limit(limit)
        result = await self.db.execute(query)
        
        items = []
        for scenario, chats_count in result.all():
            scenario.chats_count = chats_count
            items.append(scenario)
        return items

    async def get_by_character(self, character_id: UUID) -> List[Scenario]:
        chat_count_subquery = (
            select(func.count(Chat.id))
            .where(Chat.scenario_id == Scenario.id)
            .correlate(Scenario)
            .label("chats_count")
        )
        query = select(Scenario, chat_count_subquery).where(Scenario.character_id == character_id)
        result = await self.db.execute(query)
        
        items = []
        for scenario, chats_count in result.all():
            scenario.chats_count = chats_count
            items.append(scenario)
        return items

    async def get_with_count(self, id: UUID) -> Scenario | None:
        chat_count_subquery = (
            select(func.count(Chat.id))
            .where(Chat.scenario_id == Scenario.id)
            .correlate(Scenario)
            .label("chats_count")
        )
        query = select(Scenario, chat_count_subquery).where(Scenario.id == id)
        result = await self.db.execute(query)
        row = result.first()
        if not row:
            return None
        
        scenario, chats_count = row
        scenario.chats_count = chats_count
        return scenario

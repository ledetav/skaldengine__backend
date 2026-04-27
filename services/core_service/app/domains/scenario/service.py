from typing import Optional, List
from uuid import UUID
from shared.base.service import BaseService
from .repository import ScenarioRepository
from .models import Scenario
from app.domains.scenario.schemas import ScenarioCreate, ScenarioUpdate

class ScenarioService(BaseService[ScenarioRepository]):
    async def get_scenarios(self, skip: int = 0, limit: int = 100) -> List[Scenario]:
        return await self.repository.get_multi_with_counts(skip=skip, limit=limit)

    async def get_by_character(self, character_id: UUID) -> List[Scenario]:
        return await self.repository.get_by_character(character_id)

    async def create_scenario(self, scenario_in: ScenarioCreate) -> Scenario:
        scenario = await self.repository.create(obj_in=scenario_in)
        scenario.chats_count = 0
        
        from app.core.broadcast import manager
        await manager.broadcast({
            "type": "NEW_SCENARIO",
            "data": {
                "id": str(scenario.id),
                "name": scenario.name,
                "description": scenario.description,
                "internal_description": scenario.internal_description,
                "character_id": str(scenario.character_id),
                "chats_count": 0
            }
        })
        return scenario

    async def update_scenario(self, scenario_id: UUID, scenario_update: ScenarioUpdate) -> Optional[Scenario]:
        scenario = await self.repository.get(scenario_id)
        if not scenario:
            return None
        updated_obj = await self.repository.update(db_obj=scenario, obj_in=scenario_update)
        
        # Fetch with count after update to be sure
        updated = await self.repository.get_with_count(scenario_id)
        
        from app.core.broadcast import manager
        if updated:
            await manager.broadcast({
                "type": "UPDATE_SCENARIO",
                "data": {
                    "id": str(updated.id),
                    "name": updated.name,
                    "description": updated.description,
                    "internal_description": updated.internal_description,
                    "character_id": str(updated.character_id),
                    "chats_count": updated.chats_count
                }
            })
        return updated

    async def delete_scenario(self, scenario_id: UUID) -> bool:
        scenario = await self.repository.get(scenario_id)
        if not scenario:
            return False
        await self.repository.delete(id=scenario_id)
        
        from app.core.broadcast import manager
        await manager.broadcast({
            "type": "DELETE_SCENARIO",
            "data": {"id": str(scenario_id)}
        })
        return True

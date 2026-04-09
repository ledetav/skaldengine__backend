from shared.base.service import BaseService
from .repository import ScenarioRepository
from .models import Scenario
from app.schemas.scenario import ScenarioCreate, ScenarioUpdate

class ScenarioService(BaseService[ScenarioRepository]):
    async def get_scenarios(self, skip: int = 0, limit: int = 100) -> List[Scenario]:
        return await self.repository.get_multi(skip=skip, limit=limit)

    async def get_by_character(self, character_id: UUID) -> List[Scenario]:
        return await self.repository.get_by_character(character_id)

    async def create_scenario(self, scenario_in: ScenarioCreate) -> Scenario:
        return await self.repository.create(obj_in=scenario_in)

    async def update_scenario(self, scenario_id: UUID, scenario_update: ScenarioUpdate) -> Optional[Scenario]:
        scenario = await self.repository.get(scenario_id)
        if not scenario:
            return None
        return await self.repository.update(db_obj=scenario, obj_in=scenario_update)

    async def delete_scenario(self, scenario_id: UUID) -> bool:
        scenario = await self.repository.get(scenario_id)
        if not scenario:
            return False
        await self.repository.delete(id=scenario_id)
        return True

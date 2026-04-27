from typing import List, Optional
from uuid import UUID
from fastapi import status
from shared.base.controller import BaseController
from .service import ScenarioService
from .schemas import ScenarioCreate, ScenarioUpdate, ScenarioResponse, ScenarioFull
from shared.schemas.response import BaseResponse

class ScenarioController(BaseController):
    def __init__(self, scenario_service: ScenarioService):
        self.scenario_service = scenario_service

    async def get_scenarios(self, character_id: Optional[UUID] = None, skip: int = 0, limit: int = 20) -> BaseResponse:
        if character_id:
            scenarios = await self.scenario_service.get_by_character(character_id)
        else:
            scenarios = await self.scenario_service.get_scenarios()
        
        # Simple pagination for now since we have everything loaded
        total = len(scenarios)
        paged_scenarios = scenarios[skip : skip + limit]
        
        return self.handle_success(data={
            "items": [ScenarioFull.model_validate(s) for s in paged_scenarios],
            "total": total
        })

    async def create_scenario(self, scenario_in: ScenarioCreate) -> BaseResponse:
        scenario = await self.scenario_service.create_scenario(scenario_in)
        return self.handle_success(data=ScenarioFull.model_validate(scenario))

    async def get_scenario(self, scenario_id: UUID) -> BaseResponse:
        scenario = await self.scenario_service.repository.get(scenario_id)
        if not scenario:
            self.handle_error("Scenario not found", status_code=status.HTTP_404_NOT_FOUND)
        
        data = ScenarioFull.model_validate(scenario)
        print(f"DEBUG: Returning scenario: {data.model_dump()}")
        return self.handle_success(data=data)

    async def update_scenario(self, scenario_id: UUID, scenario_update: ScenarioUpdate) -> BaseResponse:
        scenario = await self.scenario_service.update_scenario(scenario_id, scenario_update)
        if not scenario:
            self.handle_error("Scenario not found", status_code=status.HTTP_404_NOT_FOUND)
        return self.handle_success(data=ScenarioFull.model_validate(scenario))

    async def delete_scenario(self, scenario_id: UUID) -> BaseResponse:
        success = await self.scenario_service.delete_scenario(scenario_id)
        if not success:
            self.handle_error("Scenario not found", status_code=status.HTTP_404_NOT_FOUND)
        return self.handle_success(data=None)

from uuid import UUID
from fastapi import APIRouter, Depends, status

from app.api import deps
from .controller import ScenarioController
from shared.schemas.response import BaseResponse
from .schemas import ScenarioCreate, ScenarioUpdate

router = APIRouter()

@router.get("/", response_model=BaseResponse)
async def list_scenarios(
    character_id: UUID | None = None,
    skip: int = 0,
    limit: int = 20,
    controller: ScenarioController = Depends(deps.get_scenario_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Получить список сценариев (с фильтром по персонажу)."""
    return await controller.get_scenarios(character_id, skip, limit)


@router.post("/", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_scenario(
    scenario_in: ScenarioCreate,
    controller: ScenarioController = Depends(deps.get_scenario_controller),
    current_user: deps.CurrentUser = Depends(deps.verify_staff_role)
):
    """Создать новый сценарий (Только для админов/модеров)."""
    return await controller.create_scenario(scenario_in)


@router.get("/{scenario_id}", response_model=BaseResponse)
async def read_scenario(
    scenario_id: UUID,
    controller: ScenarioController = Depends(deps.get_scenario_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Получить информацию о сценарии."""
    return await controller.get_scenario(scenario_id)


@router.patch("/{scenario_id}", response_model=BaseResponse)
async def update_scenario(
    scenario_id: UUID,
    scenario_in: ScenarioUpdate,
    controller: ScenarioController = Depends(deps.get_scenario_controller),
    current_user: deps.CurrentUser = Depends(deps.verify_staff_role)
):
    """Обновить сценарий (Только для админов)."""
    return await controller.update_scenario(scenario_id, scenario_in)


@router.delete("/{scenario_id}", response_model=BaseResponse, status_code=status.HTTP_200_OK)
async def delete_scenario(
    scenario_id: UUID,
    controller: ScenarioController = Depends(deps.get_scenario_controller),
    current_user: deps.CurrentUser = Depends(deps.verify_staff_role)
):
    """Удалить сценарий (Только для админов)."""
    return await controller.delete_scenario(scenario_id)

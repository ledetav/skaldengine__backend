from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api import deps
from app.models.scenario import Scenario
from app.schemas.scenario import ScenarioCreate, ScenarioUpdate, Scenario as ScenarioSchema

router = APIRouter()


@router.get("/", response_model=List[ScenarioSchema])
async def list_scenarios(
    character_id: UUID | None = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    query = select(Scenario).offset(skip).limit(limit)
    if character_id:
        query = query.where(Scenario.character_id == character_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=ScenarioSchema, status_code=status.HTTP_201_CREATED)
async def create_scenario(
    scenario_in: ScenarioCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_active_superuser)
):
    scenario = Scenario(**scenario_in.model_dump())
    db.add(scenario)
    await db.commit()
    await db.refresh(scenario)
    return scenario


@router.get("/{scenario_id}", response_model=ScenarioSchema)
async def get_scenario(
    scenario_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    scenario = await db.get(Scenario, scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.put("/{scenario_id}", response_model=ScenarioSchema)
async def update_scenario(
    scenario_id: UUID,
    scenario_update: ScenarioUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_active_superuser)
):
    scenario = await db.get(Scenario, scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    for key, value in scenario_update.model_dump(exclude_unset=True).items():
        setattr(scenario, key, value)
    db.add(scenario)
    await db.commit()
    await db.refresh(scenario)
    return scenario


@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scenario(
    scenario_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_active_superuser)
):
    scenario = await db.get(Scenario, scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    await db.delete(scenario)
    await db.commit()

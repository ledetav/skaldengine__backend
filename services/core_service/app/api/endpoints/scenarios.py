from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api import deps
from app.models.scenario import Scenario
from app.models.character import Character
from app.schemas.scenario import ScenarioCreate, ScenarioUpdate, Scenario as ScenarioSchema
from app.core.kafka import send_entity_event

router = APIRouter()

@router.get("/", response_model=List[ScenarioSchema])
async def read_scenarios(
    character_id: UUID | None = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    query = select(Scenario)
    if character_id:
        query = query.where(Scenario.owner_character_id == character_id)
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/", response_model=ScenarioSchema, status_code=status.HTTP_201_CREATED)
async def create_scenario(
    scenario_in: ScenarioCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_active_superuser)
):
    if scenario_in.owner_character_id:
        character = await db.get(Character, scenario_in.owner_character_id)
        if not character:
            raise HTTPException(status_code=404, detail="Character not found")
    
    scenario = Scenario(**scenario_in.model_dump())
    db.add(scenario)
    await db.commit()
    await db.refresh(scenario)
    
    await send_entity_event(
        event_type="Created",
        entity_type="Scenario",
        entity_id=str(scenario.id),
        payload={"title": scenario.title, "character_id": str(scenario.owner_character_id) if scenario.owner_character_id else None}
    )
    
    return scenario

@router.get("/{scenario_id}", response_model=ScenarioSchema)
async def read_scenario(
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
    
    update_data = scenario_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(scenario, key, value)
    
    db.add(scenario)
    await db.commit()
    await db.refresh(scenario)
    
    await send_entity_event(
        event_type="Updated",
        entity_type="Scenario",
        entity_id=str(scenario_id),
        payload={"updated_fields": list(update_data.keys())}
    )
    
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
    
    await send_entity_event(
        event_type="Deleted",
        entity_type="Scenario",
        entity_id=str(scenario_id),
        payload={"title": scenario.title}
    )
    
    return None

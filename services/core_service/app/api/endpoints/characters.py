from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api import deps
from app.models.character import Character
from app.schemas.character import CharacterCreate, CharacterUpdate, Character as CharacterSchema
from app.core.kafka import send_entity_event

router = APIRouter()

@router.get("/", response_model=List[CharacterSchema])
async def read_characters(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(deps.get_db),
    # Юзер может быть не авторизован для просмотра списка? Если да, можно убрать deps
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    query = select(Character).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/", response_model=CharacterSchema, status_code=status.HTTP_201_CREATED)
async def create_character(
    character_in: CharacterCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_active_superuser)
):
    character = Character(**character_in.model_dump())
    db.add(character)
    await db.commit()
    await db.refresh(character)

    await send_entity_event(
        event_type="Created",
        entity_type="Character",
        entity_id=str(character.id),
        payload={"name": character.name}
    )

    return character

@router.get("/{character_id}", response_model=CharacterSchema)
async def read_character(
    character_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    character = await db.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character

@router.put("/{character_id}", response_model=CharacterSchema)
async def update_character(
    character_id: UUID,
    character_update: CharacterUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_active_superuser)
):
    character = await db.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    update_data = character_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(character, key, value)
        
    db.add(character)
    await db.commit()
    await db.refresh(character)

    await send_entity_event(
        event_type="Updated",
        entity_type="Character",
        entity_id=str(character.id),
        payload={"updated_fields": list(update_data.keys())}
    )
    
    return character

@router.delete("/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character(
    character_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_active_superuser)
):
    character = await db.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    await db.delete(character)
    await db.commit()
    
    await send_entity_event(
        event_type="Deleted",
        entity_type="Character",
        entity_id=str(character_id),
        payload={"name": character.name}
    )
    
    return None
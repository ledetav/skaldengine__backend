from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api import deps
from app.models.user import User
from app.models.character import Character
from app.schemas.character import CharacterCreate, CharacterUpdate, Character as CharacterSchema

router = APIRouter()

@router.get("/", response_model=List[CharacterSchema])
async def read_characters(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    query = select(Character).offset(skip).limit(limit)
    result = await db.execute(query)
    characters = result.scalars().all()
    return characters

@router.post("/", response_model=CharacterSchema, status_code=status.HTTP_201_CREATED)
async def create_character(
    character_in: CharacterCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
):
    character = Character(**character_in.model_dump())
    db.add(character)
    await db.commit()
    await db.refresh(character)
    return character

@router.get("/{character_id}", response_model=CharacterSchema)
async def read_character(
    character_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    query = select(Character).where(Character.id == character_id)
    result = await db.execute(query)
    character = result.scalars().first()
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character

@router.put("/{character_id}", response_model=CharacterSchema)
async def update_character(
    character_id: UUID,
    character_update: CharacterUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
):
    query = select(Character).where(Character.id == character_id)
    result = await db.execute(query)
    character = result.scalars().first()
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    update_data = character_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(character, key, value)
        
    db.add(character)
    await db.commit()
    await db.refresh(character)
    return character
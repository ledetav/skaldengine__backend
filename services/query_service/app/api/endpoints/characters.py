from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api import deps
from app.models.read_models import CharacterReadModel
from app.schemas.read_schemas import CharacterRead

router = APIRouter()

@router.get("/", response_model=List[CharacterRead])
async def get_characters(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    query = select(CharacterReadModel).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{character_id}", response_model=CharacterRead)
async def get_character(
    character_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    character = await db.get(CharacterReadModel, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character

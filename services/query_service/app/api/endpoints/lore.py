from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api import deps
from app.models.read_models import LoreItemReadModel
from app.schemas.read_schemas import LoreItemRead

router = APIRouter()

@router.get("/{character_id}", response_model=List[LoreItemRead])
async def get_character_lore(
    character_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    query = select(LoreItemReadModel).where(LoreItemReadModel.character_id == character_id)
    result = await db.execute(query)
    return result.scalars().all()

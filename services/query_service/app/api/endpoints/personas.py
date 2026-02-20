from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api import deps
from app.models.read_models import UserPersonaReadModel
from app.schemas.read_schemas import UserPersonaRead

router = APIRouter()

@router.get("/", response_model=List[UserPersonaRead])
async def get_personas(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    query = select(UserPersonaReadModel)\
        .where(UserPersonaReadModel.owner_id == current_user.id)\
        .offset(skip)\
        .limit(limit)
        
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{persona_id}", response_model=UserPersonaRead)
async def get_persona(
    persona_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    persona = await db.get(UserPersonaReadModel, persona_id)
    if not persona or str(persona.owner_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Persona not found")
    return persona

from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api import deps
from app.models.user import User
from app.models.user_persona import UserPersona
from app.schemas.user_persona import UserPersonaCreate, UserPersonaUpdate, UserPersona as UserPersonaSchema

router = APIRouter()

@router.get("/", response_model=List[UserPersonaSchema])
async def read_personas(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user) # <--- Магия здесь
):
    """
    Получить список персон ТЕКУЩЕГО пользователя.
    Параметры skip и limit реализуют пагинацию.
    """
    query = select(UserPersona)\
        .where(UserPersona.owner_id == current_user.id)\
        .offset(skip)\
        .limit(limit)
        
    result = await db.execute(query)
    personas = result.scalars().all()
    return personas

# --- 2. CREATE (Создать свою персону) ---
@router.post("/", response_model=UserPersonaSchema, status_code=status.HTTP_201_CREATED)
async def create_persona(
    persona_in: UserPersonaCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Создать новую персону, привязанную к текущему аккаунту.
    """
    new_persona = UserPersona(
        **persona_in.model_dump(),
        owner_id=current_user.id
    )
    
    db.add(new_persona)
    await db.commit()
    await db.refresh(new_persona)
    return new_persona

@router.get("/{persona_id}", response_model=UserPersonaSchema)
async def read_persona(
    persona_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    # Ищем персону, которая имеет этот ID И принадлежит текущему юзеру
    query = select(UserPersona).where(
        UserPersona.id == persona_id,
        UserPersona.owner_id == current_user.id
    )
    result = await db.execute(query)
    persona = result.scalars().first()
    
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found or access denied")
    return persona

@router.put("/{persona_id}", response_model=UserPersonaSchema)
async def update_persona(
    persona_id: UUID,
    persona_update: UserPersonaUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    query = select(UserPersona).where(
        UserPersona.id == persona_id,
        UserPersona.owner_id == current_user.id
    )
    result = await db.execute(query)
    persona = result.scalars().first()
    
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found or access denied")
    
    update_data = persona_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(persona, key, value)
    
    db.add(persona)
    await db.commit()
    await db.refresh(persona)
    return persona

@router.delete("/{persona_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_persona(
    persona_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    query = select(UserPersona).where(
        UserPersona.id == persona_id,
        UserPersona.owner_id == current_user.id
    )
    result = await db.execute(query)
    persona = result.scalars().first()
    
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found or access denied")
    
    await db.delete(persona)
    await db.commit()
    return None
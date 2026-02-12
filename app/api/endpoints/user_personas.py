from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.api import deps
from app.models.user_persona import UserPersona
from app.schemas.user_persona import UserPersonaCreate, UserPersonaUpdate, UserPersona as UserPersonaSchema

router = APIRouter()

# --- 1. GET ALL (с пагинацией для методички и прода) ---
@router.get("/", response_model=List[UserPersonaSchema])
async def read_personas(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Получить список персон.
    Параметры skip и limit реализуют пагинацию (поэтапную загрузку).
    """
    # В будущем здесь добавим фильтр .where(UserPersona.owner_id == current_user.id)
    query = select(UserPersona).offset(skip).limit(limit)
    result = await db.execute(query)
    personas = result.scalars().all()
    return personas

# --- 2. CREATE (Добавление объекта) ---
@router.post("/", response_model=UserPersonaSchema, status_code=status.HTTP_201_CREATED)
async def create_persona(
    persona_in: UserPersonaCreate,
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Создать новую персону.
    """
    # Хардкодим owner_id пока нет авторизации.
    # В будущем: owner_id = current_user.id
    # Для теста нужно, чтобы в БД уже был user с таким UUID.
    
    # !!! ВРЕМЕННЫЙ ХАК: ищем первого попавшегося юзера, чтобы привязать персону к нему
    from app.models.user import User
    result = await db.execute(select(User).limit(1))
    first_user = result.scalars().first()
    
    if not first_user:
        raise HTTPException(status_code=400, detail="Сначала создайте хотя бы одного юзера в БД (через админку или ручками)")

    new_persona = UserPersona(
        **persona_in.model_dump(),
        owner_id=first_user.id 
    )
    
    db.add(new_persona)
    await db.commit()
    await db.refresh(new_persona)
    return new_persona

# --- 3. GET ONE (Получение одного объекта) ---
@router.get("/{persona_id}", response_model=UserPersonaSchema)
async def read_persona(
    persona_id: UUID,
    db: AsyncSession = Depends(deps.get_db)
):
    query = select(UserPersona).where(UserPersona.id == persona_id)
    result = await db.execute(query)
    persona = result.scalars().first()
    
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    return persona

# --- 4. UPDATE (Изменение объекта) ---
@router.put("/{persona_id}", response_model=UserPersonaSchema)
async def update_persona(
    persona_id: UUID,
    persona_update: UserPersonaUpdate,
    db: AsyncSession = Depends(deps.get_db)
):
    # 1. Получаем объект
    query = select(UserPersona).where(UserPersona.id == persona_id)
    result = await db.execute(query)
    persona = result.scalars().first()
    
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    # 2. Обновляем поля, если они переданы
    update_data = persona_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(persona, key, value)
    
    # 3. Сохраняем
    db.add(persona)
    await db.commit()
    await db.refresh(persona)
    return persona

# --- 5. DELETE (Удаление объекта) ---
@router.delete("/{persona_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_persona(
    persona_id: UUID,
    db: AsyncSession = Depends(deps.get_db)
):
    query = select(UserPersona).where(UserPersona.id == persona_id)
    result = await db.execute(query)
    persona = result.scalars().first()
    
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    await db.delete(persona)
    await db.commit()
    return None
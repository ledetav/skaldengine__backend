from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.api import deps
from app.models.lorebook import Lorebook, LorebookEntry
from app.models.character import Character
from app.models.user_persona import UserPersona
from app.schemas.lorebook import (
    LorebookCreate, LorebookUpdate, Lorebook as LorebookSchema,
    LorebookEntryCreate, LorebookEntryUpdate, LorebookEntry as LorebookEntrySchema
)

router = APIRouter()


# ─── Lorebooks CRUD ──────────────────────────────────────────────────────── #

@router.get("/", response_model=List[LorebookSchema])
async def list_lorebooks(
    character_id: UUID | None = None,
    fandom: str | None = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Список лорбуков."""
    query = select(Lorebook).options(selectinload(Lorebook.entries))
    
    if current_user.role not in ["admin", "moderator"]:
        # Обычный пользователь видит ТОЛЬКО свои лорбуки (через свои персоны)
        persona_ids_subquery = select(UserPersona.id).where(UserPersona.owner_id == current_user.id)
        query = query.where(Lorebook.user_persona_id.in_(persona_ids_subquery))
    else:
        # Админ и модератор могут фильтровать глобальный лор
        if character_id:
            query = query.where(Lorebook.character_id == character_id)
        if fandom:
            query = query.where(Lorebook.fandom == fandom)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().unique().all()


@router.post("/", response_model=LorebookSchema, status_code=status.HTTP_201_CREATED)
async def create_lorebook(
    lorebook_in: LorebookCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Создать новый лорбук."""
    # ── Проверка на создание глобального лора (только админ/модератор) ────────
    is_global = lorebook_in.character_id is not None or lorebook_in.fandom is not None
    if is_global and current_user.role not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="Only admins/moderators can create character or fandom lorebooks")

    # ── Проверка лимитов для персоны ──────────────────────────────────────────
    if lorebook_in.user_persona_id:
        persona = await db.get(UserPersona, lorebook_in.user_persona_id)
        if not persona or str(persona.owner_id) != str(current_user.id):
            raise HTTPException(status_code=404, detail="User persona not found or you don't own it")

        # Лимиты: admin(7), moderator(5), user(3)
        role_limits = {"admin": 7, "moderator": 5, "user": 3}
        limit = role_limits.get(current_user.role, 3)

        count_query = select(func.count()).select_from(Lorebook).where(Lorebook.user_persona_id == persona.id)
        count_res = await db.execute(count_query)
        count = count_res.scalar() or 0
        
        if count >= limit:
            raise HTTPException(
                status_code=400, 
                detail=f"Max lorebooks limit reached ({limit}) for persona."
            )
            
    if lorebook_in.character_id:
        character = await db.get(Character, lorebook_in.character_id)
        if not character:
            raise HTTPException(status_code=404, detail="Character not found")
            
    lorebook = Lorebook(**lorebook_in.model_dump())
    db.add(lorebook)
    await db.commit()
    query = select(Lorebook).options(selectinload(Lorebook.entries)).where(Lorebook.id == lorebook.id)
    result = await db.execute(query)
    return result.scalars().first()


@router.get("/{lorebook_id}", response_model=LorebookSchema)
async def get_lorebook(
    lorebook_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    query = select(Lorebook).options(selectinload(Lorebook.entries)).where(Lorebook.id == lorebook_id)
    result = await db.execute(query)
    lorebook = result.scalars().first()
    if not lorebook:
        raise HTTPException(status_code=404, detail="Lorebook not found")
    return lorebook


@router.put("/{lorebook_id}", response_model=LorebookSchema)
async def update_lorebook(
    lorebook_id: UUID,
    lorebook_update: LorebookUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_active_superuser)
):
    query = select(Lorebook).options(selectinload(Lorebook.entries)).where(Lorebook.id == lorebook_id)
    result = await db.execute(query)
    lorebook = result.scalars().first()
    if not lorebook:
        raise HTTPException(status_code=404, detail="Lorebook not found")
    for key, value in lorebook_update.model_dump(exclude_unset=True).items():
        setattr(lorebook, key, value)
    db.add(lorebook)
    await db.commit()
    query2 = select(Lorebook).options(selectinload(Lorebook.entries)).where(Lorebook.id == lorebook.id)
    result2 = await db.execute(query2)
    return result2.scalars().first()


@router.delete("/{lorebook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lorebook(
    lorebook_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_active_superuser)
):
    lorebook = await db.get(Lorebook, lorebook_id)
    if not lorebook:
        raise HTTPException(status_code=404, detail="Lorebook not found")
    await db.delete(lorebook)
    await db.commit()


# ─── LorebookEntries CRUD ────────────────────────────────────────────────── #

@router.post("/{lorebook_id}/entries", response_model=LorebookEntrySchema, status_code=status.HTTP_201_CREATED)
async def create_entry(
    lorebook_id: UUID,
    entry_in: LorebookEntryCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Добавить новый факт в лорбук."""
    lorebook = await db.get(Lorebook, lorebook_id)
    if not lorebook:
        raise HTTPException(status_code=404, detail="Lorebook not found")
        
    # Проверка прав: если это персональный лорбук, проверяем владельца. Если глобальный — только админ.
    if lorebook.user_persona_id:
        persona = await db.get(UserPersona, lorebook.user_persona_id)
        if not persona or str(persona.owner_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to modify this lorebook")
    elif current_user.role not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="Admins only for global lorebooks")

    entry = LorebookEntry(**entry_in.model_dump(), lorebook_id=lorebook_id)
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.get("/{lorebook_id}/entries", response_model=List[LorebookEntrySchema])
async def list_entries(
    lorebook_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    lorebook = await db.get(Lorebook, lorebook_id)
    if not lorebook:
        raise HTTPException(status_code=404, detail="Lorebook not found")
    query = select(LorebookEntry).where(LorebookEntry.lorebook_id == lorebook_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/{lorebook_id}/entries/{entry_id}", response_model=LorebookEntrySchema)
async def update_entry(
    lorebook_id: UUID,
    entry_id: UUID,
    entry_update: LorebookEntryUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Обновить существующий факт."""
    lorebook = await db.get(Lorebook, lorebook_id)
    if not lorebook:
        raise HTTPException(status_code=404, detail="Lorebook not found")

    if lorebook.user_persona_id:
        persona = await db.get(UserPersona, lorebook.user_persona_id)
        if not persona or str(persona.owner_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to modify this lorebook")
    elif current_user.role not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="Admins only for global lorebooks")

    entry = await db.get(LorebookEntry, entry_id)
    if not entry or entry.lorebook_id != lorebook_id:
        raise HTTPException(status_code=404, detail="Entry not found")
    for key, value in entry_update.model_dump(exclude_unset=True).items():
        setattr(entry, key, value)
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.delete("/{lorebook_id}/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(
    lorebook_id: UUID,
    entry_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Удалить факт."""
    lorebook = await db.get(Lorebook, lorebook_id)
    if not lorebook:
        raise HTTPException(status_code=404, detail="Lorebook not found")

    if lorebook.user_persona_id:
        persona = await db.get(UserPersona, lorebook.user_persona_id)
        if not persona or str(persona.owner_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to modify this lorebook")
    elif current_user.role not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="Admins only for global lorebooks")

    entry = await db.get(LorebookEntry, entry_id)
    if not entry or entry.lorebook_id != lorebook_id:
        raise HTTPException(status_code=404, detail="Entry not found")
    await db.delete(entry)
    await db.commit()

from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api import deps
from app.models.lorebook import Lorebook, LorebookEntry
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
    """Список лорбуков с фильтрацией по персонажу или фандому."""
    query = select(Lorebook)
    if character_id:
        query = query.where(Lorebook.character_id == character_id)
    if fandom:
        query = query.where(Lorebook.fandom == fandom)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=LorebookSchema, status_code=status.HTTP_201_CREATED)
async def create_lorebook(
    lorebook_in: LorebookCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_active_superuser)
):
    lorebook = Lorebook(**lorebook_in.model_dump())
    db.add(lorebook)
    await db.commit()
    await db.refresh(lorebook)
    return lorebook


@router.get("/{lorebook_id}", response_model=LorebookSchema)
async def get_lorebook(
    lorebook_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    lorebook = await db.get(Lorebook, lorebook_id)
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
    lorebook = await db.get(Lorebook, lorebook_id)
    if not lorebook:
        raise HTTPException(status_code=404, detail="Lorebook not found")
    for key, value in lorebook_update.model_dump(exclude_unset=True).items():
        setattr(lorebook, key, value)
    db.add(lorebook)
    await db.commit()
    await db.refresh(lorebook)
    return lorebook


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
    current_user: deps.CurrentUser = Depends(deps.get_current_active_superuser)
):
    lorebook = await db.get(Lorebook, lorebook_id)
    if not lorebook:
        raise HTTPException(status_code=404, detail="Lorebook not found")
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
    current_user: deps.CurrentUser = Depends(deps.get_current_active_superuser)
):
    lorebook = await db.get(Lorebook, lorebook_id)
    if not lorebook:
        raise HTTPException(status_code=404, detail="Lorebook not found")
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
    current_user: deps.CurrentUser = Depends(deps.get_current_active_superuser)
):
    entry = await db.get(LorebookEntry, entry_id)
    if not entry or entry.lorebook_id != lorebook_id:
        raise HTTPException(status_code=404, detail="Entry not found")
    await db.delete(entry)
    await db.commit()

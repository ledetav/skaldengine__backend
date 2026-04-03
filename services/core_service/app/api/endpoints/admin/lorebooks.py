import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api import deps
from app.models.lorebook import Lorebook, LorebookEntry
from app.schemas.lorebook import (
    LorebookCreate,
    Lorebook as LorebookSchema,
    LorebookEntryCreate,
    LorebookEntryUpdate,
    LorebookEntry as LorebookEntrySchema
)

router = APIRouter(dependencies=[Depends(deps.verify_admin_role)])


@router.post("/", response_model=LorebookSchema, status_code=status.HTTP_201_CREATED)
async def create_lorebook(
    *,
    db: AsyncSession = Depends(deps.get_db),
    lorebook_in: LorebookCreate,
) -> Any:
    db_obj = Lorebook(
        name=lorebook_in.name,
        character_id=lorebook_in.character_id,
        fandom=lorebook_in.fandom
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.post("/{lorebook_id}/entries", response_model=LorebookEntrySchema, status_code=status.HTTP_201_CREATED)
async def create_lorebook_entry(
    *,
    db: AsyncSession = Depends(deps.get_db),
    lorebook_id: uuid.UUID,
    entry_in: LorebookEntryCreate,
) -> Any:
    db_obj = LorebookEntry(
        lorebook_id=lorebook_id,
        keywords=entry_in.keywords,
        content=entry_in.content,
        priority=entry_in.priority
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.get("/{lorebook_id}/entries", response_model=list[LorebookEntrySchema])
async def get_lorebook_entries(
    lorebook_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    stmt = (
        select(LorebookEntry)
        .where(LorebookEntry.lorebook_id == lorebook_id)
        .order_by(LorebookEntry.priority.desc())
        .offset(skip).limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.put("/entries/{entry_id}", response_model=LorebookEntrySchema)
async def update_lorebook_entry(
    *,
    db: AsyncSession = Depends(deps.get_db),
    entry_id: uuid.UUID,
    entry_in: LorebookEntryUpdate,
) -> Any:
    result = await db.execute(select(LorebookEntry).where(LorebookEntry.id == entry_id))
    db_obj = result.scalars().first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Lorebook entry not found")
        
    update_data = entry_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
        
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lorebook_entry(
    *,
    db: AsyncSession = Depends(deps.get_db),
    entry_id: uuid.UUID,
):
    result = await db.execute(select(LorebookEntry).where(LorebookEntry.id == entry_id))
    db_obj = result.scalars().first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Lorebook entry not found")
        
    await db.delete(db_obj)
    await db.commit()

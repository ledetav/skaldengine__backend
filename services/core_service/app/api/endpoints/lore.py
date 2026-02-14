from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api import deps
from app.models.character import Character
from app.models.lore_item import LoreItem
from app.schemas.lore_item import LoreItemCreate, LoreItem as LoreItemSchema
from app.core import rag 

router = APIRouter()

@router.post("/{character_id}", response_model=LoreItemSchema)
async def create_lore_item(
    character_id: UUID,
    lore_in: LoreItemCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_active_superuser)
):
    character = await db.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
        
    new_lore = LoreItem(
        **lore_in.model_dump(),
        character_id=character_id
    )
    
    db.add(new_lore)
    await db.commit()
    await db.refresh(new_lore)
    
    # Индексация в RAG
    rag.index_lore_item(new_lore)
    
    return new_lore

@router.get("/{character_id}", response_model=List[LoreItemSchema])
async def read_character_lore(
    character_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    character = await db.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    query = select(LoreItem).where(LoreItem.character_id == character_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.delete("/{lore_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lore_item(
    lore_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_active_superuser)
):
    lore = await db.get(LoreItem, lore_id)
    if not lore:
        raise HTTPException(status_code=404, detail="Lore item not found")
        
    await db.delete(lore)
    await db.commit()
    
    rag.delete_lore_from_index(str(lore_id))
    return None
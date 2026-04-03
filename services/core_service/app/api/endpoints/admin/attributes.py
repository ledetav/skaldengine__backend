import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.api import deps
from app.models.character_attribute import CharacterAttribute
from app.models.character import Character
from app.schemas.character_attribute import (
    CharacterAttributeCreate,
    CharacterAttributeUpdate,
    CharacterAttribute as CharacterAttributeSchema,
    CharacterAttributeBulkCreate
)

router = APIRouter(dependencies=[Depends(deps.verify_admin_role)])


@router.get("/", response_model=list[CharacterAttributeSchema])
async def get_attributes(
    character_id: uuid.UUID = Query(None, description="Filter by character"),
    category: str = Query(None, description="Filter by category"),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    stmt = select(CharacterAttribute)
    if character_id:
        stmt = stmt.where(CharacterAttribute.character_id == character_id)
    if category:
        stmt = stmt.where(CharacterAttribute.category == category)
        
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=CharacterAttributeSchema, status_code=status.HTTP_201_CREATED)
async def create_attribute(
    *,
    db: AsyncSession = Depends(deps.get_db),
    attribute_in: CharacterAttributeCreate,
) -> Any:
    character = await db.get(Character, attribute_in.character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    db_obj = CharacterAttribute(
        character_id=attribute_in.character_id,
        category=attribute_in.category,
        content=attribute_in.content
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.post("/bulk", response_model=list[CharacterAttributeSchema], status_code=status.HTTP_201_CREATED)
async def create_attributes_bulk(
    *,
    db: AsyncSession = Depends(deps.get_db),
    bulk_in: CharacterAttributeBulkCreate,
) -> Any:
    character = await db.get(Character, bulk_in.character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    new_attrs = []
    for attr in bulk_in.attributes:
        db_obj = CharacterAttribute(
            character_id=bulk_in.character_id,
            category=attr.category,
            content=attr.content
        )
        db.add(db_obj)
        new_attrs.append(db_obj)
        
    await db.commit()
    for attr in new_attrs:
        await db.refresh(attr)
    return new_attrs


@router.put("/{attribute_id}", response_model=CharacterAttributeSchema)
async def update_attribute(
    *,
    db: AsyncSession = Depends(deps.get_db),
    attribute_id: uuid.UUID,
    attribute_in: CharacterAttributeUpdate,
) -> Any:
    result = await db.execute(select(CharacterAttribute).where(CharacterAttribute.id == attribute_id))
    db_obj = result.scalars().first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Attribute not found")
        
    update_data = attribute_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
        
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.delete("/{attribute_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attribute(
    *,
    db: AsyncSession = Depends(deps.get_db),
    attribute_id: uuid.UUID,
):
    result = await db.execute(select(CharacterAttribute).where(CharacterAttribute.id == attribute_id))
    db_obj = result.scalars().first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Attribute not found")
        
    await db.delete(db_obj)
    await db.commit()


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attributes_for_character(
    *,
    db: AsyncSession = Depends(deps.get_db),
    character_id: uuid.UUID = Query(..., description="Character ID to delete all attributes for"),
):
    stmt = delete(CharacterAttribute).where(CharacterAttribute.character_id == character_id)
    await db.execute(stmt)
    await db.commit()

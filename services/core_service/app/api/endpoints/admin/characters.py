import uuid
import os
import aiofiles
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api import deps
from app.core.config import settings
from app.models.character import Character
from app.schemas.character import CharacterCreate, CharacterUpdate, Character as CharacterSchema

router = APIRouter(dependencies=[Depends(deps.verify_admin_role)])
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

def validate_image(filename: str) -> str:
    ext = filename.split(".")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    return ext


@router.post("/", response_model=CharacterSchema, status_code=status.HTTP_201_CREATED)
async def create_character(
    *,
    db: AsyncSession = Depends(deps.get_db),
    character_in: CharacterCreate,
    current_user: deps.CurrentUser = Depends(deps.get_current_user),
) -> Any:
    db_obj = Character(
        creator_id=current_user.id,
        **character_in.model_dump()
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.put("/{character_id}", response_model=CharacterSchema)
async def update_character(
    *,
    db: AsyncSession = Depends(deps.get_db),
    character_id: uuid.UUID,
    character_in: CharacterUpdate,
) -> Any:
    result = await db.execute(select(Character).where(Character.id == character_id))
    db_obj = result.scalars().first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Character not found")
        
    update_data = character_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
        
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.delete("/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character(
    *,
    db: AsyncSession = Depends(deps.get_db),
    character_id: uuid.UUID,
) -> Any:
    """Soft deletes the character."""
    result = await db.execute(select(Character).where(Character.id == character_id))
    db_obj = result.scalars().first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Character not found")
        
    db_obj.is_deleted = True
    db_obj.is_public = False
    db.add(db_obj)
    await db.commit()


@router.post("/{character_id}/images", response_model=dict)
async def upload_character_images(
    *,
    db: AsyncSession = Depends(deps.get_db),
    character_id: uuid.UUID,
    avatar: UploadFile = File(None),
    card_image: UploadFile = File(None)
) -> Any:
    result = await db.execute(select(Character).where(Character.id == character_id))
    db_obj = result.scalars().first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Character not found")

    response_urls = {}

    async def save_file(file: UploadFile, prefix: str) -> str:
        ext = validate_image(file.filename)
        filename = f"{prefix}_{character_id}_{uuid.uuid4().hex[:8]}.{ext}"
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        try:
            async with aiofiles.open(file_path, 'wb') as out_file:
                while content := await file.read(1024 * 1024):
                    await out_file.write(content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")
            
        return f"/static/{filename}"

    if avatar:
        avatar_url = await save_file(avatar, "avatar")
        db_obj.avatar_url = avatar_url
        response_urls["avatar_url"] = avatar_url
        
    if card_image:
        card_url = await save_file(card_image, "card")
        db_obj.card_image_url = card_url
        response_urls["card_image_url"] = card_url

    if response_urls:
        db.add(db_obj)
        await db.commit()

    return response_urls

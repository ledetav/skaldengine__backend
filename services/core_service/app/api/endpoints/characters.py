from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.broadcast import manager

from app.api import deps
from app.models.character import Character
from app.models.chat import Chat
from app.models.scenario import Scenario
from app.schemas.character import CharacterCreate, CharacterUpdate, Character as CharacterSchema
router = APIRouter()

@router.get("/", response_model=List[CharacterSchema])
async def read_characters(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    query = select(Character).where(
        Character.is_deleted == False,
        Character.is_public == True
    ).offset(skip).limit(limit)
    result = await db.execute(query)
    characters = result.scalars().all()

    for char in characters:
        # Считаем количество сценариев
        sc_count_query = select(func.count()).select_from(Scenario).where(Scenario.character_id == char.id)
        sc_res = await db.execute(sc_count_query)
        char.scenarios_count = sc_res.scalar() or 0

        # Считаем количество чатов по сценариям
        ch_count_query = select(func.count()).select_from(Chat).where(
            Chat.character_id == char.id,
            Chat.mode == "scenario"
        )
        ch_res = await db.execute(ch_count_query)
        char.scenario_chats_count = ch_res.scalar() or 0

    return characters

@router.post("/", response_model=CharacterSchema, status_code=status.HTTP_201_CREATED)
async def create_character(
    character_in: CharacterCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_active_superuser)
):
    character = Character(**character_in.model_dump(), creator_id=current_user.id)
    db.add(character)
    await db.commit()
    await db.refresh(character)

    # Broadcast new character update
    await manager.broadcast({
        "type": "NEW_CHARACTER",
        "data": {
            "id": str(character.id),
            "name": character.name,
            "description": character.description,
            "fandom": character.fandom,
            "avatar_url": character.avatar_url,
            "card_image_url": character.card_image_url,
            "gender": character.gender,
            "nsfw_allowed": character.nsfw_allowed,
            "created_at": character.created_at.isoformat() if character.created_at else None,
            "total_chats_count": 0,
            "monthly_chats_count": 0
        }
    })

    return character

@router.get("/{character_id}", response_model=CharacterSchema)
async def read_character(
    character_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    character = await db.get(Character, character_id)
    if not character or character.is_deleted or not character.is_public:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Считаем количество сценариев
    sc_count_query = select(func.count()).select_from(Scenario).where(Scenario.character_id == character.id)
    sc_res = await db.execute(sc_count_query)
    character.scenarios_count = sc_res.scalar() or 0

    # Считаем количество чатов по сценариям
    ch_count_query = select(func.count()).select_from(Chat).where(
        Chat.character_id == character.id,
        Chat.mode == "scenario"
    )
    ch_res = await db.execute(ch_count_query)
    character.scenario_chats_count = ch_res.scalar() or 0

    return character

@router.put("/{character_id}", response_model=CharacterSchema)
async def update_character(
    character_id: UUID,
    character_update: CharacterUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_active_superuser)
):
    character = await db.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    update_data = character_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(character, key, value)
        
    db.add(character)
    await db.commit()
    await db.refresh(character)
    
    # Broadcast update
    await manager.broadcast({
        "type": "UPDATE_CHARACTER",
        "data": {
            "id": str(character.id),
            "name": character.name,
            "description": character.description,
            "fandom": character.fandom,
            "avatar_url": character.avatar_url,
            "card_image_url": character.card_image_url,
            "gender": character.gender,
            "nsfw_allowed": character.nsfw_allowed,
            "total_chats_count": character.total_chats_count,
            "monthly_chats_count": character.monthly_chats_count
        }
    })
    
    return character

@router.delete("/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character(
    character_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_active_superuser)
):
    character = await db.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    await db.delete(character)
    await db.commit()

    # Broadcast deletion
    await manager.broadcast({
        "type": "DELETE_CHARACTER",
        "data": {
            "id": str(character_id)
        }
    })

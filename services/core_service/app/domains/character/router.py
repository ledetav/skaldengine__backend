from uuid import UUID
from fastapi import APIRouter, Depends, status

from .schemas import CharacterCreate, CharacterResponse
from .controller import CharacterController
from app.api import deps
from app.schemas.response import BaseResponse
from app.schemas.character import CharacterCreate, CharacterUpdate

router = APIRouter()

@router.get("/", response_model=BaseResponse)
async def read_characters(
    skip: int = 0,
    limit: int = 20,
    controller: CharacterController = Depends(deps.get_character_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """
    Retrieve characters.
    """
    is_admin = current_user.role in ["admin", "moderator"]
    return await controller.get_characters(skip, limit, is_admin=is_admin)

@router.post("/", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_character(
    character_in: CharacterCreate,
    controller: CharacterController = Depends(deps.get_character_controller),
    current_user: deps.CurrentUser = Depends(deps.verify_staff_role)
):
    """
    Create a new character.
    """
    return await controller.create_character(character_in, current_user.id)

@router.get("/{character_id}", response_model=BaseResponse)
async def read_character(
    character_id: UUID,
    controller: CharacterController = Depends(deps.get_character_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """
    Get a specific character by ID.
    """
    is_admin = current_user.role in ["admin", "moderator"]
    return await controller.get_character(character_id, is_admin=is_admin)

@router.put("/{character_id}", response_model=BaseResponse)
async def update_character(
    character_id: UUID,
    character_update: CharacterUpdate,
    controller: CharacterController = Depends(deps.get_character_controller),
    current_user: deps.CurrentUser = Depends(deps.verify_staff_role)
):
    """
    Update a character.
    """
    return await controller.update_character(character_id, character_update)

@router.delete("/{character_id}", response_model=BaseResponse, status_code=status.HTTP_200_OK)
async def delete_character(
    character_id: UUID,
    controller: CharacterController = Depends(deps.get_character_controller),
    current_user: deps.CurrentUser = Depends(deps.verify_staff_role)
):
    """
    Delete a character.
    """
    return await controller.delete_character(character_id)

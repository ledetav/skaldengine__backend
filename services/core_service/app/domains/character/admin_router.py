import uuid
from fastapi import APIRouter, Depends, status, UploadFile, File

from app.api import deps
from .controller import CharacterController
from .schemas import CharacterCreate, CharacterUpdate
from shared.schemas.response import BaseResponse

router = APIRouter(dependencies=[Depends(deps.verify_admin_role)])

@router.post("/", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_character(
    character_in: CharacterCreate,
    controller: CharacterController = Depends(deps.get_character_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user),
) -> BaseResponse:
    """Создать нового персонажа (через админку)."""
    return await controller.create_character(character_in, current_user.id)


@router.patch("/{character_id}", response_model=BaseResponse)
async def update_character(
    character_id: uuid.UUID,
    character_in: CharacterUpdate,
    controller: CharacterController = Depends(deps.get_character_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user),
) -> BaseResponse:
    """Обновить персонажа (через админку)."""
    return await controller.update_character(character_id, character_in, current_user.id, is_admin=True)


@router.delete("/{character_id}", response_model=BaseResponse, status_code=status.HTTP_200_OK)
async def delete_character(
    character_id: uuid.UUID,
    controller: CharacterController = Depends(deps.get_character_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user),
) -> BaseResponse:
    """Мягкое удаление персонажа."""
    return await controller.delete_character(character_id, current_user.id, is_admin=True)


@router.post("/{character_id}/images", response_model=BaseResponse)
async def upload_character_images(
    character_id: uuid.UUID,
    avatar: UploadFile = File(None),
    card_image: UploadFile = File(None),
    controller: CharacterController = Depends(deps.get_character_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user),
) -> BaseResponse:
    """Загрузить аватар или карту персонажа."""
    return await controller.upload_images(character_id, avatar, card_image)

import uuid
from fastapi import APIRouter, Depends, Query, status

from app.api import deps
from .attribute_controller import CharacterAttributeController
from .attribute_schemas import (
    CharacterAttributeCreate,
    CharacterAttributeUpdate,
    CharacterAttributeBulkCreate
)
from shared.schemas.response import BaseResponse

router = APIRouter(dependencies=[Depends(deps.verify_admin_role)])

@router.get("/", response_model=BaseResponse)
async def get_attributes(
    character_id: uuid.UUID = Query(None, description="Filter by character"),
    category: str = Query(None, description="Filter by category"),
    controller: CharacterAttributeController = Depends(deps.get_character_attribute_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Получить список атрибутов (с фильтрацией)."""
    return await controller.get_attributes(character_id, category)


@router.post("/", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_attribute(
    attribute_in: CharacterAttributeCreate,
    controller: CharacterAttributeController = Depends(deps.get_character_attribute_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Создать новый атрибут."""
    return await controller.create_attribute(attribute_in)


@router.post("/bulk", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_attributes_bulk(
    bulk_in: CharacterAttributeBulkCreate,
    controller: CharacterAttributeController = Depends(deps.get_character_attribute_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Массовое создание атрибутов."""
    return await controller.create_bulk(bulk_in)


@router.get("/{attribute_id}", response_model=BaseResponse)
async def read_attribute(
    attribute_id: uuid.UUID,
    controller: CharacterAttributeController = Depends(deps.get_character_attribute_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Получить информацию о конкретном атрибуте."""
    return await controller.get_attribute(attribute_id)


@router.patch("/{attribute_id}", response_model=BaseResponse)
async def update_attribute(
    attribute_id: uuid.UUID,
    attribute_in: CharacterAttributeUpdate,
    controller: CharacterAttributeController = Depends(deps.get_character_attribute_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Обновить атрибут."""
    return await controller.update_attribute(attribute_id, attribute_in)


@router.delete("/{attribute_id}", response_model=BaseResponse, status_code=status.HTTP_200_OK)
async def delete_attribute(
    attribute_id: uuid.UUID,
    controller: CharacterAttributeController = Depends(deps.get_character_attribute_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Удалить атрибут."""
    return await controller.delete_attribute(attribute_id)


@router.delete("/", response_model=BaseResponse, status_code=status.HTTP_200_OK)
async def delete_attributes_for_character(
    character_id: uuid.UUID = Query(..., description="Character ID to delete all attributes for"),
    controller: CharacterAttributeController = Depends(deps.get_character_attribute_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Удалить все атрибуты персонажа."""
    return await controller.delete_for_character(character_id)

import uuid
from fastapi import APIRouter, Depends, status

from app.api import deps
from .controller import LorebookController
from .schemas import (
    LorebookCreate,
    LorebookEntryCreate,
    LorebookEntryUpdate
)
from app.schemas.response import BaseResponse

router = APIRouter(dependencies=[Depends(deps.verify_staff_role)])

@router.get("/check-fandom", response_model=BaseResponse)
async def check_fandom(
    name: str,
    controller: LorebookController = Depends(deps.get_lorebook_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
) -> BaseResponse:
    """Проверить существование фандомного лорбука по названию."""
    return await controller.check_fandom(name)

@router.post("/", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_lorebook(
    lorebook_in: LorebookCreate,
    controller: LorebookController = Depends(deps.get_lorebook_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
) -> BaseResponse:
    """Создать новый лорбук."""
    is_admin = current_user.role == "admin"
    return await controller.create_lorebook(lorebook_in, is_admin=is_admin)


@router.post("/{lorebook_id}/entries", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_lorebook_entry(
    lorebook_id: uuid.UUID,
    entry_in: LorebookEntryCreate,
    controller: LorebookController = Depends(deps.get_lorebook_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
) -> BaseResponse:
    """Добавить запись в лорбук."""
    return await controller.create_entry(lorebook_id, entry_in)


@router.get("/{lorebook_id}/entries", response_model=BaseResponse)
async def get_lorebook_entries(
    lorebook_id: uuid.UUID,
    controller: LorebookController = Depends(deps.get_lorebook_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
) -> BaseResponse:
    """Получить список записей лорбука."""
    lorebook = await controller.lorebook_service.get_lorebook(lorebook_id)
    if not lorebook:
        return controller.handle_error("Lorebook not found", status_code=status.HTTP_404_NOT_FOUND)
    entries = await controller.lorebook_service.entry_repository.get_by_lorebook(lorebook_id)
    return controller.handle_success(data=entries)


@router.patch("/entries/{entry_id}", response_model=BaseResponse)
async def update_lorebook_entry(
    entry_id: uuid.UUID,
    entry_in: LorebookEntryUpdate,
    controller: LorebookController = Depends(deps.get_lorebook_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
) -> BaseResponse:
    """Обновить запись лорбука."""
    is_admin = current_user.role == "admin"
    return await controller.update_entry(entry_id, entry_in) # Entries don't have role check yet, but lorebook metadata does


@router.delete("/entries/{entry_id}", response_model=BaseResponse, status_code=status.HTTP_200_OK)
async def delete_lorebook_entry(
    entry_id: uuid.UUID,
    controller: LorebookController = Depends(deps.get_lorebook_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
) -> BaseResponse:
    """Удалить запись лорбука."""
    is_admin = current_user.role == "admin"
    return await controller.delete_entry(entry_id)

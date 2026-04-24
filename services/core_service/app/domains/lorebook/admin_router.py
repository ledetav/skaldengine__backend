import uuid
from fastapi import APIRouter, Depends, status

from app.api import deps
from .controller import LorebookController
from .schemas import (
    LorebookCreate,
    LorebookUpdate,
    LorebookEntryCreate,
    LorebookEntryUpdate,
    LorebookEntryBulkCreate,
    LorebookEntry as LorebookEntrySchema
)
from shared.schemas.response import BaseResponse

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

@router.patch("/{lorebook_id}", response_model=BaseResponse)
async def update_lorebook(
    lorebook_id: uuid.UUID,
    lorebook_in: LorebookUpdate,
    controller: LorebookController = Depends(deps.get_lorebook_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
) -> BaseResponse:
    """Обновить лорбук (через админку)."""
    is_admin = current_user.role == "admin"
    return await controller.update_lorebook(lorebook_id, lorebook_in, is_admin=is_admin)

@router.delete("/{lorebook_id}", response_model=BaseResponse, status_code=status.HTTP_200_OK)
async def delete_lorebook(
    lorebook_id: uuid.UUID,
    controller: LorebookController = Depends(deps.get_lorebook_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
) -> BaseResponse:
    """Удалить лорбук (через админку)."""
    is_admin = current_user.role == "admin"
    return await controller.delete_lorebook(lorebook_id, is_admin=is_admin)


@router.post("/{lorebook_id}/entries", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_lorebook_entry(
    lorebook_id: uuid.UUID,
    entry_in: LorebookEntryCreate,
    controller: LorebookController = Depends(deps.get_lorebook_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
) -> BaseResponse:
    """Добавить запись в лорбук."""
    return await controller.create_entry(lorebook_id, entry_in)


@router.post("/{lorebook_id}/entries/bulk", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_lorebook_entries_bulk(
    lorebook_id: uuid.UUID,
    bulk_in: LorebookEntryBulkCreate,
    controller: LorebookController = Depends(deps.get_lorebook_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
) -> BaseResponse:
    """Добавить несколько записей в лорбук."""
    return await controller.create_entries_bulk(lorebook_id, bulk_in)


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
    data = [LorebookEntrySchema.model_validate(e) for e in entries]
    return controller.handle_success(data=data)


@router.patch("/{lorebook_id}/entries/{entry_id}", response_model=BaseResponse)
async def update_lorebook_entry(
    lorebook_id: uuid.UUID,
    entry_id: uuid.UUID,
    entry_in: LorebookEntryUpdate,
    controller: LorebookController = Depends(deps.get_lorebook_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
) -> BaseResponse:
    """Обновить запись лорбука."""
    is_admin = current_user.role == "admin"
    return await controller.update_entry(entry_id, entry_in) # Entries don't have role check yet, but lorebook metadata does


@router.delete("/{lorebook_id}/entries/{entry_id}", response_model=BaseResponse, status_code=status.HTTP_200_OK)
async def delete_lorebook_entry(
    lorebook_id: uuid.UUID,
    entry_id: uuid.UUID,
    controller: LorebookController = Depends(deps.get_lorebook_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
) -> BaseResponse:
    """Удалить запись лорбука."""
    is_admin = current_user.role == "admin"
    return await controller.delete_entry(entry_id)

from uuid import UUID
from fastapi import APIRouter, Depends, status

from app.api import deps
from .controller import LorebookController
from shared.schemas.response import BaseResponse
from .schemas import LorebookCreate, LorebookUpdate, LorebookEntryCreate, LorebookEntryUpdate

router = APIRouter()

@router.post("/", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_lorebook(
    lorebook_in: LorebookCreate,
    controller: LorebookController = Depends(deps.get_lorebook_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Создать новый лорбук."""
    is_admin = current_user.role == "admin"
    return await controller.create_lorebook(lorebook_in, is_admin=is_admin)


@router.get("/", response_model=BaseResponse)
async def list_lorebooks(
    character_id: UUID | None = None,
    persona_id: UUID | None = None,
    user_id: UUID | None = None,
    skip: int = 0,
    limit: int = 20,
    type: str | None = None,
    controller: LorebookController = Depends(deps.get_lorebook_controller),
    current_user: deps.CurrentUser | None = Depends(deps.get_optional_current_user)
):
    """Получить список лорбуков (с фильтрацией)."""
    return await controller.get_lorebooks(character_id, persona_id, user_id, skip=skip, limit=limit, lb_type=type)


@router.get("/{lorebook_id}", response_model=BaseResponse)
async def read_lorebook(
    lorebook_id: UUID,
    controller: LorebookController = Depends(deps.get_lorebook_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Получить информацию о лорбуке и его записи."""
    return await controller.get_lorebook(lorebook_id)


@router.patch("/{lorebook_id}", response_model=BaseResponse)
async def update_lorebook(
    lorebook_id: UUID,
    lorebook_update: LorebookUpdate,
    controller: LorebookController = Depends(deps.get_lorebook_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Обновить метаданные лорбука."""
    is_admin = current_user.role == "admin"
    return await controller.update_lorebook(lorebook_id, lorebook_update, is_admin=is_admin)


@router.delete("/{lorebook_id}", response_model=BaseResponse, status_code=status.HTTP_200_OK)
async def delete_lorebook(
    lorebook_id: UUID,
    controller: LorebookController = Depends(deps.get_lorebook_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Удалить лорбук."""
    is_admin = current_user.role == "admin"
    return await controller.delete_lorebook(lorebook_id, is_admin=is_admin)


# ─── Lorebook Entries ─────────────────────────────────────────────────────── #

@router.post("/{lorebook_id}/entries", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_entry(
    lorebook_id: UUID,
    entry_in: LorebookEntryCreate,
    controller: LorebookController = Depends(deps.get_lorebook_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Добавить запись в лорбук."""
    return await controller.create_entry(lorebook_id, entry_in)


@router.post("/{lorebook_id}/entries/bulk", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_entries_bulk(
    lorebook_id: UUID,
    bulk_in: LorebookEntryBulkCreate,
    controller: LorebookController = Depends(deps.get_lorebook_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Добавить сразу несколько записей в лорбук."""
    return await controller.create_entries_bulk(lorebook_id, bulk_in)


@router.patch("/{lorebook_id}/entries/{entry_id}", response_model=BaseResponse)
async def update_entry(
    lorebook_id: UUID,
    entry_id: UUID,
    entry_update: LorebookEntryUpdate,
    controller: LorebookController = Depends(deps.get_lorebook_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Обновить запись в лорбуке."""
    return await controller.update_entry(entry_id, entry_update)


@router.delete("/{lorebook_id}/entries/{entry_id}", response_model=BaseResponse, status_code=status.HTTP_200_OK)
async def delete_entry(
    lorebook_id: UUID,
    entry_id: UUID,
    controller: LorebookController = Depends(deps.get_lorebook_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Удалить запись из лорбука."""
    return await controller.delete_entry(entry_id)


@router.get("/{lorebook_id}/entries", response_model=BaseResponse)
async def list_entries(
    lorebook_id: UUID,
    skip: int = 0,
    limit: int = 20,
    controller: LorebookController = Depends(deps.get_lorebook_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Получить список записей лорбука (пагинированный)."""
    return await controller.get_entries(lorebook_id, skip=skip, limit=limit)


@router.get("/{lorebook_id}/entries/{entry_id}", response_model=BaseResponse)
async def read_entry(
    lorebook_id: UUID,
    entry_id: UUID,
    controller: LorebookController = Depends(deps.get_lorebook_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Получить информацию о конкретной записи лорбука."""
    return await controller.get_entry(entry_id)

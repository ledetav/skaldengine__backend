from uuid import UUID
from fastapi import APIRouter, Depends, status

from app.api import deps
from .controller import LorebookController
from app.schemas.response import BaseResponse
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
    controller: LorebookController = Depends(deps.get_lorebook_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Получить список лорбуков (с фильтрацией)."""
    return await controller.get_lorebooks(character_id, persona_id)


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


@router.patch("/entries/{entry_id}", response_model=BaseResponse)
async def update_entry(
    entry_id: UUID,
    entry_update: LorebookEntryUpdate,
    controller: LorebookController = Depends(deps.get_lorebook_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Обновить запись в лорбуке."""
    return await controller.update_entry(entry_id, entry_update)


@router.delete("/entries/{entry_id}", response_model=BaseResponse, status_code=status.HTTP_200_OK)
async def delete_entry(
    entry_id: UUID,
    controller: LorebookController = Depends(deps.get_lorebook_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Удалить запись из лорбука."""
    return await controller.delete_entry(entry_id)

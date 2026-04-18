from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from .message_controller import MessageController
from app.schemas.response import BaseResponse
from pydantic import BaseModel

router = APIRouter()

class MessageEdit(BaseModel):
    new_content: str

@router.post("/{parent_id}/regenerate/stream")
async def regenerate_message_stream(
    parent_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    controller: MessageController = Depends(deps.get_message_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """
    Генерирует альтернативный ответ (Свайп).
    """
    return await controller.regenerate_stream(parent_id, current_user.id, db)


@router.put("/{message_id}", response_model=BaseResponse)
async def edit_message(
    message_id: UUID,
    message_in: MessageEdit,
    db: AsyncSession = Depends(deps.get_db),
    controller: MessageController = Depends(deps.get_message_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """
    Редактирование истории (Непрямое ветвление).
    """
    return await controller.edit_message(message_id, message_in.new_content, current_user.id, db)


@router.post("/{message_id}/fork", response_model=BaseResponse)
async def fork_chat_at(
    message_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    controller: MessageController = Depends(deps.get_message_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """
    Явное ветвление (Форк в новый чат).
    """
    return await controller.fork_chat(message_id, current_user.id, db)


@router.get("/{message_id}", response_model=BaseResponse)
async def read_message(
    message_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    controller: MessageController = Depends(deps.get_message_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """
    Получить конкретное сообщение по ID.
    """
    return await controller.get_message(message_id, current_user.id, db)


@router.delete("/{message_id}", response_model=BaseResponse)
async def delete_message(
    message_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    controller: MessageController = Depends(deps.get_message_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """
    Удалить сообщение из истории.
    """
    return await controller.delete_message(message_id, current_user.id, db)

from uuid import UUID
from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from .controller import ChatController
from .message_controller import MessageController
from app.schemas.response import BaseResponse
from .schemas import ChatCreate, ChatUpdate
from .message_schemas import MessageCreate

router = APIRouter()

@router.post("/", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    chat_in: ChatCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(deps.get_db),
    controller: ChatController = Depends(deps.get_chat_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Создать новый чат с AI-персонажем."""
    return await controller.create_chat(chat_in, current_user.id, background_tasks, db)


@router.get("/", response_model=BaseResponse)
async def list_chats(
    skip: int = 0,
    limit: int = 20,
    controller: ChatController = Depends(deps.get_chat_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Получить список чатов пользователя."""
    return await controller.get_user_chats(current_user.id, skip, limit)


@router.get("/{chat_id}", response_model=BaseResponse)
async def read_chat(
    chat_id: UUID,
    controller: ChatController = Depends(deps.get_chat_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Получить информацию о конкретном чате."""
    return await controller.get_chat(chat_id, current_user.id)


@router.patch("/{chat_id}", response_model=BaseResponse)
async def update_chat(
    chat_id: UUID,
    chat_in: ChatUpdate,
    controller: ChatController = Depends(deps.get_chat_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Обновить настройки чата или название."""
    return await controller.update_chat(chat_id, chat_in, current_user.id)


@router.delete("/{chat_id}", response_model=BaseResponse, status_code=status.HTTP_200_OK)
async def delete_chat(
    chat_id: UUID,
    controller: ChatController = Depends(deps.get_chat_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Удалить чат."""
    return await controller.delete_chat(chat_id, current_user.id)


@router.post("/{chat_id}/messages/stream")
async def send_message_stream(
    chat_id: UUID,
    message_in: MessageCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(deps.get_db),
    controller: MessageController = Depends(deps.get_message_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Отправить сообщение и получить ответ AI SSE."""
    return await controller.send_message_stream(chat_id, current_user.id, message_in, background_tasks, db)


@router.get("/{chat_id}/history", response_model=BaseResponse)
async def get_chat_history(
    chat_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    controller: ChatController = Depends(deps.get_chat_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Получить историю сообщений и дерево веток."""
    return await controller.get_history(chat_id, current_user.id, db)

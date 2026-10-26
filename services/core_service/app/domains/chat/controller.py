"""
Контроллер API для работы с ролевыми чатами (Chat).
"""

from typing import List, Optional
from fastapi import BackgroundTasks, status
from uuid import UUID
from shared.base.controller import BaseController
from .service import ChatService
from .schemas import ChatCreate, ChatUpdate, ChatResponse
from shared.schemas.response import BaseResponse
from sqlalchemy.ext.asyncio import AsyncSession


class ChatController(BaseController):
    """
    Контроллер запросов для управления чатами и получением дерева сообщений.
    """
    def __init__(self, chat_service: ChatService):
        self.chat_service = chat_service

    async def create_chat(self, chat_in: ChatCreate, user_id: UUID, background_tasks: BackgroundTasks, db: AsyncSession) -> BaseResponse:
        """Создать новый чат с персонажем."""
        try:
            chat = await self.chat_service.create_chat(chat_in, user_id, background_tasks, db)
            return self.handle_success(data=ChatResponse.model_validate(chat))
        except (ValueError, PermissionError) as e:
            self.handle_error(str(e))

    async def get_user_chats(self, user_id: UUID, skip: int = 0, limit: int = 20) -> BaseResponse:
        """Получить список чатов текущего пользователя."""
        chats = await self.chat_service.get_user_chats(user_id, skip, limit)
        return self.handle_success(data=chats)

    async def get_chat(self, chat_id: UUID, user_id: UUID) -> BaseResponse:
        """Получить данные конкретного чата."""
        chat = await self.chat_service.get_chat(chat_id, user_id)
        if not chat:
            self.handle_error("Chat not found", status_code=status.HTTP_404_NOT_FOUND)
        return self.handle_success(data=ChatResponse.model_validate(chat))

    async def update_chat(self, chat_id: UUID, chat_update: ChatUpdate, user_id: UUID) -> BaseResponse:
        """Обновить настройки или метаданные чата."""
        chat = await self.chat_service.update_chat(chat_id, chat_update, user_id)
        if not chat:
            self.handle_error("Chat not found", status_code=status.HTTP_404_NOT_FOUND)
        return self.handle_success(data=ChatResponse.model_validate(chat))

    async def delete_chat(self, chat_id: UUID, user_id: UUID) -> BaseResponse:
        """Удалить чат."""
        success = await self.chat_service.delete_chat(chat_id, user_id)
        if not success:
            self.handle_error("Chat not found", status_code=status.HTTP_404_NOT_FOUND)
        return self.handle_success(data=None)

    async def get_history(self, chat_id: UUID, user_id: UUID, db: AsyncSession) -> BaseResponse:
        """Получить дерево сообщений, активную ветку диалога и контрольные точки."""
        try:
            payload = await self.chat_service.get_history_payload(chat_id, user_id, db)
            return self.handle_success(data=payload)
        except ValueError as e:
            self.handle_error(str(e), status_code=status.HTTP_404_NOT_FOUND)


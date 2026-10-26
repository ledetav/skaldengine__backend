"""
Контроллер API для работы с сообщениями (Message): стриминг, свайпы, редактирование и форки.
"""

from typing import List, Optional, Any
from uuid import UUID
from fastapi import status, BackgroundTasks
from fastapi.responses import StreamingResponse
from shared.base.controller import BaseController
from .message_service import MessageService
from .message_schemas import MessageCreate, MessageResponse
from .schemas import ChatResponse
from shared.schemas.response import BaseResponse
from sqlalchemy.ext.asyncio import AsyncSession


class MessageController(BaseController):
    """
    Контроллер запросов для взаимодействия с сообщениями чата.
    """
    def __init__(self, message_service: MessageService):
        self.message_service = message_service

    async def send_message_stream(
        self, chat_id: UUID, current_user: Any, message_in: MessageCreate, 
        background_tasks: BackgroundTasks, db: AsyncSession
    ) -> StreamingResponse:
        """Отправить сообщение и вернуть ответ ИИ через SSE-поток."""
        try:
            generator = await self.message_service.send_message_stream(chat_id, current_user, message_in, background_tasks, db)
            return StreamingResponse(generator, media_type="text/event-stream")
        except ValueError as e:
            self.handle_error(str(e), status_code=status.HTTP_404_NOT_FOUND)

    async def regenerate_stream(self, parent_id: UUID, current_user: Any, db: AsyncSession) -> StreamingResponse:
        """Перегенерировать ответ ассистента в виде SSE-потока (свайп)."""
        try:
            generator = await self.message_service.regenerate_stream(parent_id, current_user, db)
            return StreamingResponse(generator, media_type="text/event-stream")
        except ValueError as e:
            self.handle_error(str(e), status_code=status.HTTP_404_NOT_FOUND)

    async def edit_message(self, message_id: UUID, new_content: str, user_id: UUID, db: AsyncSession) -> BaseResponse:
        """Редактировать сообщение с созданием новой ветки."""
        try:
            new_msg = await self.message_service.edit_message(message_id, new_content, user_id, db)
            return self.handle_success(data=MessageResponse.model_validate(new_msg))
        except ValueError as e:
            self.handle_error(str(e), status_code=status.HTTP_404_NOT_FOUND)

    async def fork_chat(self, message_id: UUID, user_id: UUID, db: AsyncSession) -> BaseResponse:
        """Форкнуть диалог из выбранного сообщения в новый чат."""
        try:
            new_chat = await self.message_service.fork_chat(message_id, user_id, db)
            return self.handle_success(data=ChatResponse.model_validate(new_chat))
        except (ValueError, PermissionError) as e:
            self.handle_error(str(e), status_code=status.HTTP_404_NOT_FOUND)

    async def get_message(self, message_id: UUID, user_id: UUID, db: AsyncSession) -> BaseResponse:
        """Получить конкретное сообщение по ID."""
        message = await self.message_service.get_message(message_id, user_id, db)
        if not message:
            self.handle_error("Message not found", status_code=status.HTTP_404_NOT_FOUND)
        return self.handle_success(data=MessageResponse.model_validate(message))

    async def delete_message(self, message_id: UUID, user_id: UUID, db: AsyncSession) -> BaseResponse:
        """Удалить сообщение по ID."""
        success = await self.message_service.delete_message(message_id, user_id, db)
        if not success:
            self.handle_error("Message not found", status_code=status.HTTP_404_NOT_FOUND)
        return self.handle_success(data={"message": "Message deleted successfully"})


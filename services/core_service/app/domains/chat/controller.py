from typing import List, Optional
from uuid import UUID
from shared.base.controller import BaseController
from .service import ChatService
from .schemas import ChatCreate, ChatResponse
from app.schemas.response import BaseResponse
from sqlalchemy.ext.asyncio import AsyncSession

class ChatController(BaseController):
    def __init__(self, chat_service: ChatService):
        self.chat_service = chat_service

    async def create_chat(self, chat_in: ChatCreate, user_id: UUID, background_tasks: BackgroundTasks, db: AsyncSession) -> BaseResponse:
        try:
            chat = await self.chat_service.create_chat(chat_in, user_id, background_tasks, db)
            return self.handle_success(data=chat)
        except (ValueError, PermissionError) as e:
            self.handle_error(str(e))

    async def get_user_chats(self, user_id: UUID, skip: int = 0, limit: int = 20) -> BaseResponse:
        chats = await self.chat_service.get_user_chats(user_id, skip, limit)
        return self.handle_success(data=chats)

    async def get_chat(self, chat_id: UUID, user_id: UUID) -> BaseResponse:
        chat = await self.chat_service.get_chat(chat_id, user_id)
        if not chat:
            self.handle_error("Chat not found", status_code=status.HTTP_404_NOT_FOUND)
        return self.handle_success(data=chat)

    async def update_chat(self, chat_id: UUID, chat_update: ChatUpdate, user_id: UUID) -> BaseResponse:
        chat = await self.chat_service.update_chat(chat_id, chat_update, user_id)
        if not chat:
            self.handle_error("Chat not found", status_code=status.HTTP_404_NOT_FOUND)
        return self.handle_success(data=chat)

    async def delete_chat(self, chat_id: UUID, user_id: UUID) -> BaseResponse:
        success = await self.chat_service.delete_chat(chat_id, user_id)
        if not success:
            self.handle_error("Chat not found", status_code=status.HTTP_404_NOT_FOUND)
        return self.handle_success(data=None)

    async def get_history(self, chat_id: UUID, user_id: UUID, db: AsyncSession) -> BaseResponse:
        try:
            payload = await self.chat_service.get_history_payload(chat_id, user_id, db)
            return self.handle_success(data=payload)
        except ValueError as e:
            self.handle_error(str(e), status_code=status.HTTP_404_NOT_FOUND)

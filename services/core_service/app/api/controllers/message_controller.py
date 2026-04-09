from typing import List, Optional
from uuid import UUID
from fastapi import status, BackgroundTasks
from app.api.base_controller import BaseController
from app.services.message_service import MessageService
from app.schemas.message import MessageCreate
from app.schemas.response import BaseResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import StreamingResponse

class MessageController(BaseController):
    def __init__(self, message_service: MessageService):
        self.message_service = message_service

    async def send_message_stream(
        self, chat_id: UUID, user_id: UUID, message_in: MessageCreate, 
        background_tasks: BackgroundTasks, db: AsyncSession
    ) -> StreamingResponse:
        try:
            generator = await self.message_service.send_message_stream(chat_id, user_id, message_in, background_tasks, db)
            return StreamingResponse(generator, media_type="text/event-stream")
        except ValueError as e:
            self.handle_error(str(e), status_code=status.HTTP_404_NOT_FOUND)

    async def regenerate_stream(self, parent_id: UUID, user_id: UUID, db: AsyncSession) -> StreamingResponse:
        try:
            generator = await self.message_service.regenerate_stream(parent_id, user_id, db)
            return StreamingResponse(generator, media_type="text/event-stream")
        except ValueError as e:
            self.handle_error(str(e), status_code=status.HTTP_404_NOT_FOUND)

    async def edit_message(self, message_id: UUID, new_content: str, user_id: UUID, db: AsyncSession) -> BaseResponse:
        try:
            new_msg = await self.message_service.edit_message(message_id, new_content, user_id, db)
            return self.handle_success(data=new_msg)
        except ValueError as e:
            self.handle_error(str(e), status_code=status.HTTP_404_NOT_FOUND)

    async def fork_chat(self, message_id: UUID, user_id: UUID, db: AsyncSession) -> BaseResponse:
        try:
            new_chat = await self.message_service.fork_chat(message_id, user_id, db)
            return self.handle_success(data=new_chat)
        except (ValueError, PermissionError) as e:
            self.handle_error(str(e), status_code=status.HTTP_404_NOT_FOUND)

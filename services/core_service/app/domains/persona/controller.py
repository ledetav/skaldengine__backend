from typing import List, Optional
from uuid import UUID
from fastapi import status
from shared.base.controller import BaseController
from .service import UserPersonaService
from .schemas import UserPersonaCreate, UserPersonaResponse
from app.schemas.user import UserStatistics
from app.schemas.response import BaseResponse

class UserPersonaController(BaseController):
    def __init__(self, persona_service: UserPersonaService):
        self.persona_service = persona_service

    async def get_my_personas(self, user_id: UUID) -> BaseResponse:
        personas = await self.persona_service.get_user_personas(user_id)
        return self.handle_success(data=personas)

    async def create_persona(self, persona_in: UserPersonaCreate, user_id: UUID) -> BaseResponse:
        persona = await self.persona_service.create_persona(persona_in, user_id)
        return self.handle_success(data=persona, status_code=status.HTTP_201_CREATED)

    async def get_persona(self, persona_id: UUID, user_id: UUID) -> BaseResponse:
        persona = await self.persona_service.get_persona(persona_id, user_id)
        if not persona:
            self.handle_error("Persona not found", status_code=status.HTTP_404_NOT_FOUND)
        return self.handle_success(data=persona)

    async def update_persona(self, persona_id: UUID, persona_update: UserPersonaUpdate, user_id: UUID) -> BaseResponse:
        persona = await self.persona_service.update_persona(persona_id, persona_update, user_id)
        if not persona:
            self.handle_error("Persona not found", status_code=status.HTTP_404_NOT_FOUND)
        return self.handle_success(data=persona)

    async def delete_persona(self, persona_id: UUID, user_id: UUID) -> BaseResponse:
        success = await self.persona_service.delete_persona(persona_id, user_id)
        if not success:
            self.handle_error("Persona not found", status_code=status.HTTP_404_NOT_FOUND)
        return self.handle_success(data=None)

    async def get_user_stats(self, user_id: UUID) -> BaseResponse:
        stats = await self.persona_service.get_user_stats(user_id)
        return self.handle_success(data=UserStatistics(**stats))

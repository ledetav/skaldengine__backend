from typing import List, Optional, Any
from uuid import UUID
from fastapi import status
from shared.base.controller import BaseController
from .service import CharacterService
from app.domains.lorebook.service import LorebookService
from app.domains.character.schemas import CharacterCreate, CharacterUpdate, CharacterRead, CharacterAdminRead
from shared.schemas.response import BaseResponse

class CharacterController(BaseController):
    def __init__(self, character_service: CharacterService, lorebook_service: LorebookService):
        self.character_service = character_service
        self.lorebook_service = lorebook_service

    async def get_characters(self, skip: int = 0, limit: int = 20, is_admin: bool = False) -> BaseResponse:
        characters = await self.character_service.get_characters(skip, limit)
        schema = CharacterAdminRead if is_admin else CharacterRead
        # Приводим к соответствующим схемам для фильтрации полей
        data = [schema.model_validate(c) for c in characters]
        return self.handle_success(data=data)

    async def get_character(self, character_id: UUID, is_admin: bool = False) -> BaseResponse:
        character = await self.character_service.get_character(character_id)
        if not character:
            self.handle_error("Character not found", status_code=status.HTTP_404_NOT_FOUND)
        
        schema = CharacterAdminRead if is_admin else CharacterRead
        data = schema.model_validate(character)
        return self.handle_success(data=data)

    async def create_character(self, character_in: CharacterCreate, user_id: UUID, is_admin: bool = False) -> BaseResponse:
        # Если это не админ (модератор), проверяем наличие фандомного лорбука
        if not is_admin and character_in.fandom:
            fandom_lb = await self.lorebook_service.get_fandom_lorebook(character_in.fandom)
            if not fandom_lb:
                self.handle_error(
                    f"Фандом '{character_in.fandom}' не найден. "
                    "Модераторы могут создавать персонажей только для существующих фандомов с лорбуком. "
                    "Обратитесь к администратору для создания фандома.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        character = await self.character_service.create_character(character_in, user_id)
        return self.handle_success(data=character)

    async def update_character(self, character_id: UUID, character_update: CharacterUpdate, user_id: UUID, is_admin: bool = False) -> BaseResponse:
        creator_id = None if is_admin else user_id
        character = await self.character_service.update_character(character_id, character_update, creator_id)
        if not character:
            self.handle_error("Character not found or access denied", status_code=status.HTTP_404_NOT_FOUND)
        return self.handle_success(data=character)

    async def delete_character(self, character_id: UUID, user_id: UUID, is_admin: bool = False) -> BaseResponse:
        creator_id = None if is_admin else user_id
        success = await self.character_service.delete_character(character_id, creator_id)
        if not success:
            self.handle_error("Character not found or access denied", status_code=status.HTTP_404_NOT_FOUND)
        return self.handle_success(data=None)

    async def upload_images(self, character_id: UUID, avatar_file: Any = None, card_file: Any = None) -> BaseResponse:
        character = await self.character_service.repository.get(character_id)
        if not character:
            self.handle_error("Character not found", status_code=status.HTTP_404_NOT_FOUND)
        
        response_urls = {}
        update_data = {}
        
        if avatar_file:
            content = await avatar_file.read()
            url = await self.character_service.save_character_image(character_id, content, avatar_file.filename, "avatar")
            update_data["avatar_url"] = url
            response_urls["avatar_url"] = url
            
        if card_file:
            content = await card_file.read()
            url = await self.character_service.save_character_image(character_id, content, card_file.filename, "card")
            update_data["card_image_url"] = url
            response_urls["card_image_url"] = url
            
        if update_data:
            await self.character_service.update_character(character_id, CharacterUpdate(**update_data))
            
        return self.handle_success(data=response_urls)

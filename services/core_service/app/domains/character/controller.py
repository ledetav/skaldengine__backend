"""
Контроллер API для работы с персонажами (Character).
"""

from typing import List, Any
from uuid import UUID
import httpx
from fastapi import status
from shared.base.controller import BaseController
from .service import CharacterService
from app.domains.lorebook.service import LorebookService
from app.domains.character.schemas import CharacterCreate, CharacterUpdate, CharacterRead, CharacterAdminRead
from shared.schemas.response import BaseResponse
from app.core.config import settings


class CharacterController(BaseController):
    """
    Контроллер запросов для управления персонажами: чтение каталога,
    создание, редактирование, удаление, загрузка изображений и обогащение авторами.
    """
    def __init__(self, character_service: CharacterService, lorebook_service: LorebookService):
        """Инициализирует контроллер персонажей внедренными сервисами персонажей и лорбуков."""
        self.character_service = character_service
        self.lorebook_service = lorebook_service

    async def get_characters(self, skip: int = 0, limit: int = 20, is_admin: bool = False) -> BaseResponse:
        """Получить список персонажей с фильтрацией по правам доступа и обогащением авторами."""
        characters, total = await self.character_service.get_characters(skip, limit, is_admin=is_admin)
        schema = CharacterAdminRead if is_admin else CharacterRead
        # Приводим к соответствующим схемам для фильтрации полей
        items = [schema.model_validate(c) for c in characters]

        # Обогащаем публичными данными авторов из auth_service
        await self._enrich_with_authors(items)

        return self.handle_success(data={"items": items, "total": total})

    async def get_character(self, character_id: UUID, is_admin: bool = False) -> BaseResponse:
        """Получить персонажа по ID с обогащением данными автора."""
        character = await self.character_service.get_character(character_id, is_admin=is_admin)
        if not character:
            self.handle_error("Character not found", status_code=status.HTTP_404_NOT_FOUND)
        schema = CharacterAdminRead if is_admin else CharacterRead
        item = schema.model_validate(character)

        # Обогащаем публичными данными автора
        await self._enrich_with_authors([item])

        return self.handle_success(data=item)

    async def _enrich_with_authors(self, items: List[Any]) -> None:
        """Пакетно подтягивает данные авторов (username, full_name, avatar_url) из auth_service."""
        creator_ids = list({str(item.creator_id) for item in items if getattr(item, "creator_id", None)})
        if not creator_ids:
            return
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.AUTH_BASE_URL}{settings.API_V1_STR}/users/batch",
                    params={"ids": ",".join(creator_ids)},
                    timeout=3.0
                )
                if resp.status_code == 200:
                    users_list = resp.json().get("data", [])
                    users_map = {str(u["id"]): u for u in users_list}
                    for item in items:
                        cid = str(item.creator_id) if getattr(item, "creator_id", None) else None
                        if cid and cid in users_map:
                            item.author = users_map[cid]
        except Exception as e:
            import logging
            logging.getLogger("core").error(f"Failed to enrich characters with authors: {e}")

    async def create_character(self, character_in: CharacterCreate, user_id: UUID, is_admin: bool = False) -> BaseResponse:
        """Создать персонажа с проверкой фандомного лорбука для модераторов."""
        # Если это не админ (модератор), проверяем наличие фандомного лорбука
        if not is_admin and character_in.fandom:
            fandom_lb = await self.lorebook_service.get_fandom_lorebook(character_in.fandom)
            if not fandom_lb:
                self.handle_error(
                    f"Moderators cannot create characters for a new fandom '{character_in.fandom}'. Ask an Admin to create the fandom lorebook first.",
                    status_code=status.HTTP_403_FORBIDDEN
                )

        character = await self.character_service.create_character(character_in, user_id)
        return self.handle_success(data=CharacterAdminRead.model_validate(character))

    async def update_character(self, character_id: UUID, character_update: CharacterUpdate, user_id: UUID, is_admin: bool = False) -> BaseResponse:
        """Обновить данные персонажа с проверкой прав."""
        creator_id = None if is_admin else user_id
        character = await self.character_service.update_character(character_id, character_update, creator_id)
        if not character:
            self.handle_error("Character not found or access denied", status_code=status.HTTP_404_NOT_FOUND)
        schema = CharacterAdminRead if is_admin else CharacterRead
        return self.handle_success(data=schema.model_validate(character))

    async def delete_character(self, character_id: UUID, user_id: UUID, is_admin: bool = False) -> BaseResponse:
        """Удалить персонажа."""
        creator_id = None if is_admin else user_id
        success = await self.character_service.delete_character(character_id, creator_id)
        if not success:
            self.handle_error("Character not found or access denied", status_code=status.HTTP_404_NOT_FOUND)
        return self.handle_success(data=None)

    async def upload_images(self, character_id: UUID, avatar_file: Any = None, card_file: Any = None) -> BaseResponse:
        """Загрузить аватар и/или карту персонажа."""
        character = await self.character_service.repository.get(character_id)
        if not character:
            self.handle_error("Character not found", status_code=status.HTTP_404_NOT_FOUND)

        update_data = {}
        response_urls = {}

        if avatar_file:
            content = await avatar_file.read()
            url = await self.character_service.save_character_image(
                character_id, content, avatar_file.filename, "avatar"
            )
            update_data["avatar_url"] = url
            response_urls["avatar_url"] = url

        if card_file:
            content = await card_file.read()
            url = await self.character_service.save_character_image(
                character_id, content, card_file.filename, "card"
            )
            update_data["card_image_url"] = url
            response_urls["card_image_url"] = url

        if update_data:
            await self.character_service.update_character(character_id, CharacterUpdate(**update_data))

        return self.handle_success(data=response_urls)

from typing import List, Optional
from uuid import UUID

from shared.base.service import BaseService
from .repository import CharacterRepository
from .models import Character
from app.domains.character.schemas import CharacterCreate, CharacterUpdate
from app.core.broadcast import manager

class CharacterService(BaseService[CharacterRepository]):
    async def get_characters(self, skip: int = 0, limit: int = 20, is_admin: bool = False) -> List[Character]:
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        query = select(Character).options(selectinload(Character.lorebooks)).where(
            Character.is_deleted == False
        )
        if not is_admin:
            query = query.where(Character.is_public == True)
            
        query = query.offset(skip).limit(limit)
        result = await self.repository.db.execute(query)
        characters = list(result.scalars().all())
        for char in characters:
            char.scenarios_count = await self.repository.get_scenarios_count(char.id)
            char.scenario_chats_count = await self.repository.get_scenario_chats_count(char.id)
        return characters

    async def get_character(self, character_id: UUID, is_admin: bool = False) -> Optional[Character]:
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        query = select(Character).options(selectinload(Character.lorebooks)).where(Character.id == character_id)
        result = await self.repository.db.execute(query)
        character = result.scalar_one_or_none()
        
        if not character:
            return None
            
        if not is_admin and (character.is_deleted or not character.is_public):
            return None
        
        character.scenarios_count = await self.repository.get_scenarios_count(character.id)
        character.scenario_chats_count = await self.repository.get_scenario_chats_count(character.id)
        return character


    async def create_character(self, character_in: CharacterCreate, creator_id: UUID) -> Character:
        data = character_in.model_dump(exclude={"lorebook_ids"})
        lorebook_ids = character_in.lorebook_ids or []
        
        character = Character(**data, creator_id=creator_id)
        
        # Load lorebooks to associate
        if lorebook_ids:
            from app.domains.lorebook.models import Lorebook
            from sqlalchemy import select
            query = select(Lorebook).where(Lorebook.id.in_(lorebook_ids))
            result = await self.repository.db.execute(query)
            character.lorebooks = list(result.scalars().all())

        created = await self.repository.create(obj_in=character)
        
        # Автоматическое создание/назначение базового лорбука для "original" персонажа
        from app.domains.character.models import CharacterType
        if created.type == CharacterType.ORIGINAL:
            try:
                from app.domains.lorebook.models import Lorebook, LorebookType
                
                # Ensure lorebooks are loaded
                await self.repository.db.refresh(created, ["lorebooks"])
                
                # Filter out shared fandom lorebooks if any (Requirement: unbind fandom lbs for original chars)
                # Note: On creation, there shouldn't be many, but just in case.
                fandom_lbs = [lb for lb in created.lorebooks if lb.type == LorebookType.FANDOM]
                if fandom_lbs:
                    created.lorebooks = [lb for lb in created.lorebooks if lb.type != LorebookType.FANDOM]
                    await self.repository.db.flush()

                # Find existing character-type lorebooks
                personal_lbs = [lb for lb in created.lorebooks if lb.type == LorebookType.CHARACTER]
                
                if not personal_lbs:
                    from app.domains.lorebook.repository import LorebookRepository
                    
                    db_session = self.repository.db
                    lorebook_repo = LorebookRepository(db_session)
                    
                    lorebook = Lorebook(
                        name=f"Основной {created.name}",
                        type=LorebookType.CHARACTER,
                        character_id=created.id,
                        description=f"Базовый лорбук персонажа {created.name}",
                        fandom=None,
                        tags=["main"]
                    )
                    lorebook.characters = [created] # Link via M2M table
                    await lorebook_repo.create(obj_in=lorebook)
                    # Refresh created to include new lorebook
                    await self.repository.db.refresh(created, ["lorebooks"])
                else:
                    # Если есть персональные лорбуки, убедимся что первый из них имеет тег main
                    has_main = any("main" in (getattr(lb, "tags", []) or []) for lb in personal_lbs)
                    if not has_main:
                         lb = personal_lbs[0]
                         if lb.tags is None: lb.tags = []
                         if "main" not in lb.tags:
                              lb.tags = list(lb.tags) + ["main"]
                              await self.repository.db.flush()
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to manage lorebook for original character {created.id}: {e}")

        # Ensure lorebooks are loaded for broadcast
        await self.repository.db.refresh(created, ["lorebooks"])

        # Broadcast new character update
        await manager.broadcast({
            "type": "NEW_CHARACTER",
            "data": self._format_broadcast_data(created)
        })
        return created

    async def update_character(self, character_id: UUID, character_update: CharacterUpdate, creator_id: Optional[UUID] = None) -> Optional[Character]:
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        
        # Need to load with lorebooks to update them
        query = select(Character).where(Character.id == character_id).options(selectinload(Character.lorebooks))
        result = await self.repository.db.execute(query)
        character = result.scalar_one_or_none()
        
        if not character:
            return None
        if creator_id and str(character.creator_id) != str(creator_id):
            return None
        
        update_data = character_update.model_dump(exclude={"lorebook_ids"}, exclude_unset=True)
        lorebook_ids = character_update.lorebook_ids
        
        if lorebook_ids is not None:
            from app.domains.lorebook.models import Lorebook
            lb_query = select(Lorebook).where(Lorebook.id.in_(lorebook_ids))
            lb_result = await self.repository.db.execute(lb_query)
            new_lorebooks = list(lb_result.scalars().all())
            
        updated = await self.repository.update(db_obj=character, obj_in=update_data)

        # Handle "Original" fandom logic for updates
        from app.domains.character.models import CharacterType
        if updated.type == CharacterType.ORIGINAL:
            from app.domains.lorebook.models import Lorebook, LorebookType
            
            # 1. Отвязываем все фандомные лорбуки
            updated.lorebooks = [lb for lb in updated.lorebooks if lb.type != LorebookType.FANDOM]
            
            # 2. Ищем существующие персональные лорбуки
            personal_lbs = [lb for lb in updated.lorebooks if lb.type == LorebookType.CHARACTER]
            
            if personal_lbs:
                # Берем первый (сортируем по дате создания, если поле есть в БД)
                if hasattr(personal_lbs[0], 'created_at'):
                    personal_lbs.sort(key=lambda x: getattr(x, 'created_at', x.id))
                
                # Делаем его основным (ставим тег main)
                target_lb = personal_lbs[0]
                has_main = any("main" in (getattr(lb, "tags", []) or []) for lb in personal_lbs)
                
                if not has_main:
                    if target_lb.tags is None: target_lb.tags = []
                    if "main" not in target_lb.tags:
                        target_lb.tags = list(target_lb.tags) + ["main"]
                        await self.repository.db.flush()
                # Мы НЕ создаем новый лорбук, так как персональные лорбуки уже есть
            else:
                # 3. Если лорбуков персонажа нет, создаем новый
                new_lb = Lorebook(
                    name=f"Основной {updated.name}",
                    type=LorebookType.CHARACTER,
                    character_id=updated.id,
                    description=f"Основной лорбук персонажа {updated.name}",
                    fandom=None,
                    tags=["main"]
                )
                self.repository.db.add(new_lb)
                await self.repository.db.flush()
                # Link it
                updated.lorebooks.append(new_lb)

        
        # Ensure lorebooks are loaded for broadcast
        await self.repository.db.refresh(updated, ["lorebooks"])
        
        # Broadcast update
        await manager.broadcast({
            "type": "UPDATE_CHARACTER",
            "data": self._format_broadcast_data(updated)
        })
        return updated

    async def delete_character(self, character_id: UUID, creator_id: Optional[UUID] = None) -> bool:
        character = await self.repository.get(character_id)
        if not character:
            return False
        if creator_id and str(character.creator_id) != str(creator_id):
            return False
        
        # Find and delete personal lorebooks associated with this character
        from app.domains.lorebook.models import Lorebook
        from sqlalchemy import delete, select
        
        # Get IDs of lorebooks being deleted to broadcast updates
        lb_query = select(Lorebook.id).where(Lorebook.character_id == character_id)
        lb_ids_result = await self.repository.db.execute(lb_query)
        deleted_lb_ids = list(lb_ids_result.scalars().all())

        lb_delete_query = delete(Lorebook).where(Lorebook.character_id == character_id)
        await self.repository.db.execute(lb_delete_query)
        
        # Soft delete character
        await self.repository.update(db_obj=character, obj_in={"is_deleted": True, "is_public": False})
        
        # Broadcast lorebook deletions
        for lb_id in deleted_lb_ids:
            await manager.broadcast({
                "type": "DELETE_LOREBOOK",
                "data": {"id": str(lb_id)}
            })

        # Broadcast deletion
        await manager.broadcast({
            "type": "DELETE_CHARACTER",
            "data": {"id": str(character_id)}
        })
        return True

    async def save_character_image(self, character_id: UUID, file_content: bytes, filename: str, prefix: str) -> str:
        import os
        import aiofiles
        from app.core.config import settings
        import uuid
        
        ext = filename.split(".")[-1].lower()
        unique_filename = f"{prefix}_{character_id}_{uuid.uuid4().hex[:8]}.{ext}"
        file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
        
        async with aiofiles.open(file_path, 'wb') as out_file:
            await out_file.write(file_content)
            
        return f"/static/{unique_filename}"


    def _format_broadcast_data(self, character: Character) -> dict:
        # Use __dict__ to check for loaded attributes without triggering lazy loads
        lorebook_ids = []
        if "lorebooks" in character.__dict__:
            lorebook_ids = [str(lb.id) for lb in character.lorebooks]
            
        return {
            "id": str(character.id),
            "name": character.name,
            "description": character.description,
            "fandom": character.fandom,
            "avatar_url": character.avatar_url,
            "card_image_url": character.card_image_url,
            "gender": character.gender,
            "nsfw_allowed": character.nsfw_allowed,
            "is_public": character.is_public,
            "is_deleted": character.is_deleted,
            "creator_id": str(character.creator_id) if character.creator_id else None,
            "total_chats_count": getattr(character, "total_chats_count", 0),
            "monthly_chats_count": getattr(character, "monthly_chats_count", 0),
            "scenarios_count": getattr(character, "scenarios_count", 0),
            "scenario_chats_count": getattr(character, "scenario_chats_count", 0),
            "lorebook_ids": lorebook_ids
        }


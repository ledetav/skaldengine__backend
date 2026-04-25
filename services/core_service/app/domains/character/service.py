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
        
        # Автоматическое создание базового лорбука для "original" персонажа
        is_original = created.fandom and (created.fandom.lower() == "original" or created.fandom.lower() == "оригинальный")
        if is_original:
            try:
                from app.domains.lorebook.models import Lorebook, LorebookType
                
                # Check if character already has an associated character-type lorebook
                has_personal_lb = any(lb.type == LorebookType.CHARACTER for lb in created.lorebooks)
                
                if not has_personal_lb:
                    from app.domains.lorebook.repository import LorebookRepository
                    
                    db_session = self.repository.db
                    lorebook_repo = LorebookRepository(db_session)
                    
                    lorebook = Lorebook(
                        name=f"Основной {created.name}",
                        type=LorebookType.CHARACTER,
                        character_id=created.id,
                        description=f"Базовый лорбук персонажа {created.name}",
                        fandom="Original",
                        tags=["main"]
                    )
                    lorebook.characters = [created] # Link via M2M table
                    await lorebook_repo.create(obj_in=lorebook)
                    # Refresh created to include new lorebook in broadcast
                    await self.repository.db.refresh(created, ["lorebooks"])
                else:
                    # Если персональный лорбук уже есть, убедимся что у него есть тег main
                    personal_lbs = [lb for lb in created.lorebooks if lb.type == LorebookType.CHARACTER]
                    has_main = any("main" in (getattr(lb, "tags", []) or []) for lb in personal_lbs)
                    if not has_main and personal_lbs:
                         lb = personal_lbs[0]
                         if lb.tags is None: lb.tags = []
                         if "main" not in lb.tags:
                              lb.tags = list(lb.tags) + ["main"]
                              # No explicit save here, it will be saved downstream or we can flush
                              await self.repository.db.flush()
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to create default lorebook for original character {created.id}: {e}")

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
            
            # Enforce "main" lorebook for Original characters (Requirement 2)
            fandom_val = update_data.get("fandom") or character.fandom
            is_original = fandom_val and (fandom_val.lower() == "original" or fandom_val.lower() == "оригинальный")
            if is_original:
                # Find current main lorebook(s)
                main_lbs = [lb for lb in character.lorebooks if "main" in (getattr(lb, "tags", []) or [])]
                for mlb in main_lbs:
                    if mlb not in new_lorebooks:
                        new_lorebooks.append(mlb)
            
            character.lorebooks = new_lorebooks
        
        # Handle "Original" fandom logic for updates
        fandom_val = update_data.get("fandom") or character.fandom
        is_original = fandom_val and (fandom_val.lower() == "original" or fandom_val.lower() == "оригинальный")
        
        if is_original:
            from app.domains.lorebook.models import Lorebook, LorebookType
            # Check if character already has an associated character-type lorebook
            personal_lbs = [lb for lb in character.lorebooks if lb.type == LorebookType.CHARACTER and lb.character_id == character.id]
            
            if not personal_lbs:
                # Create default personal lorebook
                new_lb = Lorebook(
                    name=f"Основной {update_data.get('name') or character.name}",
                    type=LorebookType.CHARACTER,
                    character_id=character.id,
                    description=f"Основной лорбук персонажа {update_data.get('name') or character.name}",
                    fandom="Original",
                    tags=["main"]
                )
                self.repository.db.add(new_lb)
                await self.repository.db.flush()
                # Link it
                character.lorebooks.append(new_lb)
            else:
                # Убедимся, что хотя бы один персональный лорбук имеет тег main
                has_main = any("main" in (getattr(lb, "tags", []) or []) for lb in personal_lbs)
                if not has_main:
                    first_lb = personal_lbs[0]
                    if first_lb.tags is None: first_lb.tags = []
                    if "main" not in first_lb.tags:
                        first_lb.tags = list(first_lb.tags) + ["main"]
                        await self.repository.db.flush()
        
        updated = await self.repository.update(db_obj=character, obj_in=update_data)

        
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
        
        # Soft delete
        await self.repository.update(db_obj=character, obj_in={"is_deleted": True, "is_public": False})
        
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
            "created_at": character.created_at.isoformat() if character.created_at else None,
            "total_chats_count": getattr(character, "total_chats_count", 0),
            "monthly_chats_count": getattr(character, "monthly_chats_count", 0),
            "scenarios_count": getattr(character, "scenarios_count", 0),
            "scenario_chats_count": getattr(character, "scenario_chats_count", 0),
            "lorebook_ids": lorebook_ids
        }


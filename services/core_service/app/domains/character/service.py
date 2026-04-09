from shared.base.service import BaseService
from .repository import CharacterRepository
from .models import Character
from app.schemas.character import CharacterCreate, CharacterUpdate
from app.core.broadcast import manager

class CharacterService(BaseService[CharacterRepository]):
    async def get_characters(self, skip: int = 0, limit: int = 20) -> List[Character]:
        characters = await self.repository.get_active_characters(skip, limit)
        for char in characters:
            char.scenarios_count = await self.repository.get_scenarios_count(char.id)
            char.scenario_chats_count = await self.repository.get_scenario_chats_count(char.id)
        return characters

    async def get_character(self, character_id: UUID) -> Optional[Character]:
        character = await self.repository.get(character_id)
        if not character or character.is_deleted or not character.is_public:
            return None
        
        character.scenarios_count = await self.repository.get_scenarios_count(character.id)
        character.scenario_chats_count = await self.repository.get_scenario_chats_count(character.id)
        return character

    async def create_character(self, character_in: CharacterCreate, creator_id: UUID) -> Character:
        character = Character(**character_in.model_dump(), creator_id=creator_id)
        created = await self.repository.create(obj_in=character)
        
        # Broadcast new character update
        await manager.broadcast({
            "type": "NEW_CHARACTER",
            "data": self._format_broadcast_data(created)
        })
        return created

    async def update_character(self, character_id: UUID, character_update: CharacterUpdate, creator_id: Optional[UUID] = None) -> Optional[Character]:
        character = await self.repository.get(character_id)
        if not character:
            return None
        if creator_id and str(character.creator_id) != str(creator_id):
            return None
        
        updated = await self.repository.update(db_obj=character, obj_in=character_update)
        
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
        return {
            "id": str(character.id),
            "name": character.name,
            "description": character.description,
            "fandom": character.fandom,
            "avatar_url": character.avatar_url,
            "card_image_url": character.card_image_url,
            "gender": character.gender,
            "nsfw_allowed": character.nsfw_allowed,
            "created_at": character.created_at.isoformat() if character.created_at else None,
            "total_chats_count": getattr(character, "total_chats_count", 0),
            "monthly_chats_count": getattr(character, "monthly_chats_count", 0)
        }

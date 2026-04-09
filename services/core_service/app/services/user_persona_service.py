from typing import List, Optional
from uuid import UUID
from app.services.base_service import BaseService
from app.repositories.user_persona_repository import UserPersonaRepository
from app.models.user_persona import UserPersona
from app.schemas.user_persona import UserPersonaCreate, UserPersonaUpdate

class UserPersonaService(BaseService[UserPersonaRepository]):
    async def get_user_personas(self, owner_id: UUID) -> List[UserPersona]:
        return await self.repository.get_by_owner(owner_id)

    async def create_persona(self, persona_in: UserPersonaCreate, owner_id: UUID) -> UserPersona:
        persona_data = persona_in.model_dump()
        persona_data["owner_id"] = owner_id
        return await self.repository.create(obj_in=persona_data)

    async def get_persona(self, persona_id: UUID, owner_id: UUID) -> Optional[UserPersona]:
        persona = await self.repository.get(persona_id)
        if persona and str(persona.owner_id) == str(owner_id):
            return persona
        return None

    async def update_persona(self, persona_id: UUID, persona_update: UserPersonaUpdate, owner_id: UUID) -> Optional[UserPersona]:
        persona = await self.get_persona(persona_id, owner_id)
        if not persona:
            return None
        return await self.repository.update(db_obj=persona, obj_in=persona_update)

    async def delete_persona(self, persona_id: UUID, owner_id: UUID) -> bool:
        persona = await self.get_persona(persona_id, owner_id)
        if not persona:
            return False
        await self.repository.delete(id=persona_id)
        return True

    async def get_user_stats(self, owner_id: UUID) -> dict:
        return await self.repository.get_aggregate_stats(owner_id)

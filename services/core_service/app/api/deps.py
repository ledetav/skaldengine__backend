from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel
from uuid import UUID
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession


from app.core.config import settings
from app.db.base import AsyncSessionLocal

# Repositories
from app.repositories.character_repository import CharacterRepository
from app.repositories.chat_repository import ChatRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.scenario_repository import ScenarioRepository
from app.repositories.user_persona_repository import UserPersonaRepository
from app.repositories.lorebook_repository import LorebookRepository, LorebookEntryRepository
from app.repositories.character_attribute_repository import CharacterAttributeRepository

# Services
from app.services.character_service import CharacterService
from app.services.chat_service import ChatService
from app.services.message_service import MessageService
from app.services.scenario_service import ScenarioService
from app.services.user_persona_service import UserPersonaService
from app.services.lorebook_service import LorebookService
from app.services.character_attribute_service import CharacterAttributeService

# Controllers
from app.api.controllers.character_controller import CharacterController
from app.api.controllers.chat_controller import ChatController
from app.api.controllers.message_controller import MessageController
from app.api.controllers.scenario_controller import ScenarioController
from app.api.controllers.user_persona_controller import UserPersonaController
from app.api.controllers.lorebook_controller import LorebookController
from app.api.controllers.character_attribute_controller import CharacterAttributeController

class CurrentUser(BaseModel):
    id: UUID
    role: str = "user"
    login: str | None = None
    username: str | None = None
    full_name: str | None = None
    birth_date: date | None = None

security = HTTPBearer()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(token_auth: HTTPAuthorizationCredentials = Depends(security)) -> CurrentUser:
    token = token_auth.credentials
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = payload.get("sub")
        if token_data is None:
             raise HTTPException(status_code=403, detail="Invalid token")
        
        # Parse birth_date
        birth_date_str = payload.get("birth_date")
        birth_date_val = None
        if birth_date_str:
            try:
                birth_date_val = date.fromisoformat(birth_date_str)
            except ValueError:
                pass

        return CurrentUser(
            id=UUID(token_data),
            role=payload.get("role", "user"),
            login=payload.get("login"),
            username=payload.get("username"),
            full_name=payload.get("full_name"),
            birth_date=birth_date_val
        )
    except (JWTError, ValueError):
        raise HTTPException(status_code=403, detail="Could not validate credentials")

async def verify_staff_role(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Allow both admins and moderators."""
    if current_user.role not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user

async def verify_admin_role(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Allow ONLY admins."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="This operation requires Administrator privileges")
    return current_user

# DI for Character
async def get_character_repository(db: AsyncSession = Depends(get_db)) -> CharacterRepository:
    return CharacterRepository(db)

async def get_character_service(repo: CharacterRepository = Depends(get_character_repository)) -> CharacterService:
    return CharacterService(repo)

async def get_character_controller(
    service: CharacterService = Depends(get_character_service),
    lorebook_service: LorebookService = Depends(get_lorebook_service)
) -> CharacterController:
    return CharacterController(service, lorebook_service)

# DI for Chat
async def get_chat_repository(db: AsyncSession = Depends(get_db)) -> ChatRepository:
    return ChatRepository(db)

async def get_chat_service(repo: ChatRepository = Depends(get_chat_repository)) -> ChatService:
    return ChatService(repo)

async def get_chat_controller(service: ChatService = Depends(get_chat_service)) -> ChatController:
    return ChatController(service)

# DI for Message
async def get_message_repository(db: AsyncSession = Depends(get_db)) -> MessageRepository:
    return MessageRepository(db)

async def get_message_service(repo: MessageRepository = Depends(get_message_repository)) -> MessageService:
    return MessageService(repo)

async def get_message_controller(service: MessageService = Depends(get_message_service)) -> MessageController:
    return MessageController(service)

# DI for Scenario
async def get_scenario_repository(db: AsyncSession = Depends(get_db)) -> ScenarioRepository:
    return ScenarioRepository(db)

async def get_scenario_service(repo: ScenarioRepository = Depends(get_scenario_repository)) -> ScenarioService:
    return ScenarioService(repo)

async def get_scenario_controller(service: ScenarioService = Depends(get_scenario_service)) -> ScenarioController:
    return ScenarioController(service)

# DI for UserPersona
async def get_user_persona_repository(db: AsyncSession = Depends(get_db)) -> UserPersonaRepository:
    return UserPersonaRepository(db)

async def get_user_persona_service(repo: UserPersonaRepository = Depends(get_user_persona_repository)) -> UserPersonaService:
    return UserPersonaService(repo)

async def get_user_persona_controller(service: UserPersonaService = Depends(get_user_persona_service)) -> UserPersonaController:
    return UserPersonaController(service)

# DI for Lorebook
async def get_lorebook_repository(db: AsyncSession = Depends(get_db)) -> LorebookRepository:
    return LorebookRepository(db)

async def get_lorebook_entry_repository(db: AsyncSession = Depends(get_db)) -> LorebookEntryRepository:
    return LorebookEntryRepository(db)

async def get_lorebook_service(
    repo: LorebookRepository = Depends(get_lorebook_repository),
    entry_repo: LorebookEntryRepository = Depends(get_lorebook_entry_repository)
) -> LorebookService:
    return LorebookService(repo, entry_repo)

async def get_lorebook_controller(service: LorebookService = Depends(get_lorebook_service)) -> LorebookController:
    return LorebookController(service)

# DI for CharacterAttribute
async def get_character_attribute_repository(db: AsyncSession = Depends(get_db)) -> CharacterAttributeRepository:
    return CharacterAttributeRepository(db)

async def get_character_attribute_service(repo: CharacterAttributeRepository = Depends(get_character_attribute_repository)) -> CharacterAttributeService:
    return CharacterAttributeService(repo)

async def get_character_attribute_controller(service: CharacterAttributeService = Depends(get_character_attribute_service)) -> CharacterAttributeController:
    return CharacterAttributeController(service)
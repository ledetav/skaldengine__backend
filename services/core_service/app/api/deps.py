"""Зависимости FastAPI (Dependencies) и внедрение зависимостей (DI) для Core Service."""

from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel, Field
from uuid import UUID
import logging
import httpx
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.core.config import settings
from app.db.base import AsyncSessionLocal

# Репозитории
from app.domains.character.repository import CharacterRepository
from app.domains.chat.repository import ChatRepository
from app.domains.chat.message_repository import MessageRepository
from app.domains.scenario.repository import ScenarioRepository
from app.domains.persona.repository import UserPersonaRepository
from app.domains.lorebook.repository import LorebookRepository, LorebookEntryRepository

# Сервисы
from app.domains.character.service import CharacterService
from app.domains.chat.service import ChatService
from app.domains.chat.message_service import MessageService
from app.domains.scenario.service import ScenarioService
from app.domains.persona.service import UserPersonaService
from app.domains.lorebook.service import LorebookService

# Контроллеры
from app.domains.character.controller import CharacterController
from app.domains.chat.controller import ChatController
from app.domains.chat.message_controller import MessageController
from app.domains.scenario.controller import ScenarioController
from app.domains.persona.controller import UserPersonaController
from app.domains.lorebook.controller import LorebookController


class CurrentUser(BaseModel):
    """Данные текущего аутентифицированного пользователя, извлеченные из JWT-токена."""
    id: UUID = Field(..., description="Идентификатор пользователя")
    role: str = Field("user", description="Роль пользователя: user, moderator, admin")
    login: str | None = Field(None, description="Логин")
    username: str | None = Field(None, description="Публичный никнейм")
    full_name: str | None = Field(None, description="Полное имя")
    birth_date: date | None = Field(None, description="Дата рождения")


security = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Генератор асинхронной сессии базы данных."""
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(token_auth: HTTPAuthorizationCredentials = Depends(security)) -> CurrentUser:
    """Извлекает и валидирует данные пользователя из Bearer JWT токена.

    Args:
        token_auth: Учетные данные авторизации HTTP Bearer.

    Returns:
        CurrentUser: Объект текущего пользователя.

    Raises:
        HTTPException: Если токен невалиден или просрочен.
    """
    token = token_auth.credentials
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = payload.get("sub")
        if token_data is None:
            raise HTTPException(status_code=403, detail="Недействительный токен")
        
        # Парсинг даты рождения
        birth_date_str = payload.get("birth_date")
        birth_date_val = None
        if birth_date_str:
            try:
                birth_date_val = date.fromisoformat(birth_date_str)
            except ValueError:
                logger.warning(f"Некорректный формат birth_date в токене: {birth_date_str}")

        return CurrentUser(
            id=UUID(token_data),
            role=payload.get("role", "user"),
            login=payload.get("login"),
            username=payload.get("username"),
            full_name=payload.get("full_name"),
            birth_date=birth_date_val
        )
    except (JWTError, ValueError):
        raise HTTPException(status_code=403, detail="Не удалось подтвердить учетные данные")


async def get_fresh_current_user(token_auth: HTTPAuthorizationCredentials = Depends(security)) -> CurrentUser:
    """Получает пользователя из токена и запрашивает актуальную роль в микросервисе Auth Service.

    Args:
        token_auth: Учетные данные авторизации.

    Returns:
        CurrentUser: Актуализированные данные пользователя.
    """
    base_user = await get_current_user(token_auth)
    # Запрашиваем свежую роль напрямую из сервиса аутентификации
    auth_url = f"{settings.AUTH_BASE_URL}{settings.API_V1_STR}/users/me"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(auth_url, headers={"Authorization": f"Bearer {token_auth.credentials}"}, timeout=2.0)
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                if "role" in data:
                    base_user.role = data["role"]
    except Exception as e:
        logger.error(f"Не удалось получить свежую информацию о пользователе из auth_service: {e}")
    return base_user


async def verify_staff_role(current_user: CurrentUser = Depends(get_fresh_current_user)) -> CurrentUser:
    """Проверяет права персонала (доступно для admin и moderator).

    Raises:
        HTTPException: Если у пользователя недостаточно прав.
    """
    if current_user.role not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="У пользователя недостаточно прав доступа")
    return current_user


async def verify_admin_role(current_user: CurrentUser = Depends(get_fresh_current_user)) -> CurrentUser:
    """Проверяет права администратора (доступно ТОЛЬКО для роли admin).

    Raises:
        HTTPException: Если пользователь не является администратором.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Данная операция требует прав администратора")
    return current_user


# Внедрение зависимостей для Lorebook (определено в начале, так как Character зависит от Lorebook)
async def get_lorebook_repository(db: AsyncSession = Depends(get_db)) -> LorebookRepository:
    """Внедрение LorebookRepository."""
    return LorebookRepository(db)


async def get_lorebook_entry_repository(db: AsyncSession = Depends(get_db)) -> LorebookEntryRepository:
    """Внедрение LorebookEntryRepository."""
    return LorebookEntryRepository(db)


async def get_lorebook_service(
    repo: LorebookRepository = Depends(get_lorebook_repository),
    entry_repo: LorebookEntryRepository = Depends(get_lorebook_entry_repository)
) -> LorebookService:
    """Внедрение LorebookService."""
    return LorebookService(repo, entry_repo)


async def get_lorebook_controller(service: LorebookService = Depends(get_lorebook_service)) -> LorebookController:
    """Внедрение LorebookController."""
    return LorebookController(service)


# Внедрение зависимостей для Character
async def get_character_repository(db: AsyncSession = Depends(get_db)) -> CharacterRepository:
    """Внедрение CharacterRepository."""
    return CharacterRepository(db)


async def get_character_service(repo: CharacterRepository = Depends(get_character_repository)) -> CharacterService:
    """Внедрение CharacterService."""
    return CharacterService(repo)


async def get_character_controller(
    service: CharacterService = Depends(get_character_service),
    lorebook_service: LorebookService = Depends(get_lorebook_service)
) -> CharacterController:
    """Внедрение CharacterController."""
    return CharacterController(service, lorebook_service)


# Внедрение зависимостей для Chat
async def get_chat_repository(db: AsyncSession = Depends(get_db)) -> ChatRepository:
    """Внедрение ChatRepository."""
    return ChatRepository(db)


async def get_chat_service(repo: ChatRepository = Depends(get_chat_repository)) -> ChatService:
    """Внедрение ChatService."""
    return ChatService(repo)


async def get_chat_controller(service: ChatService = Depends(get_chat_service)) -> ChatController:
    """Внедрение ChatController."""
    return ChatController(service)


# Внедрение зависимостей для Message
async def get_message_repository(db: AsyncSession = Depends(get_db)) -> MessageRepository:
    """Внедрение MessageRepository."""
    return MessageRepository(db)


async def get_message_service(repo: MessageRepository = Depends(get_message_repository)) -> MessageService:
    """Внедрение MessageService."""
    return MessageService(repo)


async def get_message_controller(service: MessageService = Depends(get_message_service)) -> MessageController:
    """Внедрение MessageController."""
    return MessageController(service)


# Внедрение зависимостей для Scenario
async def get_scenario_repository(db: AsyncSession = Depends(get_db)) -> ScenarioRepository:
    """Внедрение ScenarioRepository."""
    return ScenarioRepository(db)


async def get_scenario_service(repo: ScenarioRepository = Depends(get_scenario_repository)) -> ScenarioService:
    """Внедрение ScenarioService."""
    return ScenarioService(repo)


async def get_scenario_controller(service: ScenarioService = Depends(get_scenario_service)) -> ScenarioController:
    """Внедрение ScenarioController."""
    return ScenarioController(service)


# Внедрение зависимостей для UserPersona
async def get_user_persona_repository(db: AsyncSession = Depends(get_db)) -> UserPersonaRepository:
    """Внедрение UserPersonaRepository."""
    return UserPersonaRepository(db)


async def get_user_persona_service(repo: UserPersonaRepository = Depends(get_user_persona_repository)) -> UserPersonaService:
    """Внедрение UserPersonaService."""
    return UserPersonaService(repo)


async def get_user_persona_controller(service: UserPersonaService = Depends(get_user_persona_service)) -> UserPersonaController:
    """Внедрение UserPersonaController."""
    return UserPersonaController(service)
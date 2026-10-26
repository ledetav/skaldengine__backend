"""Зависимости FastAPI (Dependencies) для микросервиса аутентификации."""

from typing import AsyncGenerator, Any
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.db.base import AsyncSessionLocal
from app.domains.user.models import User
from app.domains.user.repository import UserRepository
from app.domains.user.auth_service import AuthService
from app.domains.user.service import UserService
from app.domains.user.auth_controller import AuthController
from app.domains.user.controller import UserController

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Генератор асинхронной сессии базы данных."""
    async with AsyncSessionLocal() as session:
        yield session


async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """Внедрение экземпляра UserRepository."""
    return UserRepository(db)


async def get_auth_service(repo: UserRepository = Depends(get_user_repository)) -> AuthService:
    """Внедрение сервиса аутентификации AuthService."""
    return AuthService(repo)


async def get_user_service(repo: UserRepository = Depends(get_user_repository)) -> UserService:
    """Внедрение сервиса управления пользователями UserService."""
    return UserService(repo)


async def get_auth_controller(service: AuthService = Depends(get_auth_service)) -> AuthController:
    """Внедрение контроллера аутентификации AuthController."""
    return AuthController(service)


async def get_user_controller(service: UserService = Depends(get_user_service)) -> UserController:
    """Внедрение контроллера пользователей UserController."""
    return UserController(service)


async def get_current_user(
    repo: UserRepository = Depends(get_user_repository),
    token: str = Depends(reusable_oauth2)
) -> User:
    """Извлекает и валидирует текущего авторизованного пользователя из JWT-токена.

    Args:
        repo: Репозиторий пользователей.
        token: JWT-токен из заголовка Authorization.

    Returns:
        User: Модель аутентифицированного пользователя.

    Raises:
        HTTPException: Если токен невалиден или пользователь не найден.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = payload.get("sub")
        if token_data is None:
            raise HTTPException(status_code=403, detail="Недействительный токен")
        token_user_id = UUID(token_data) 
    except (JWTError, ValueError): 
        raise HTTPException(status_code=403, detail="Не удалось подтвердить учетные данные")
        
    user = await repo.get(token_user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return user
from typing import AsyncGenerator, Any
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.db.base import AsyncSessionLocal
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.api.controllers.auth_controller import AuthController
from app.api.controllers.user_controller import UserController

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

async def get_auth_service(repo: UserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(repo)

async def get_user_service(repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(repo)

async def get_auth_controller(service: AuthService = Depends(get_auth_service)) -> AuthController:
    return AuthController(service)

async def get_user_controller(service: UserService = Depends(get_user_service)) -> UserController:
    return UserController(service)

async def get_current_user(
    repo: UserRepository = Depends(get_user_repository),
    token: str = Depends(reusable_oauth2)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = payload.get("sub")
        if token_data is None:
             raise HTTPException(status_code=403, detail="Invalid token")
        token_user_id = UUID(token_data) 
    except (JWTError, ValueError): 
        raise HTTPException(status_code=403, detail="Could not validate credentials")
        
    user = await repo.get(token_user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user
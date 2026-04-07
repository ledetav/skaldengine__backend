from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserResponse

router = APIRouter()

@router.post("/login", response_model=Token)
async def login_access_token(
    db: AsyncSession = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    # Ищем пользователя по email или login
    query = select(User).where(
        or_(User.email == form_data.username, User.login == form_data.username)
    )
    result = await db.execute(query)
    user = result.scalars().first()

    # Проверяем пароль
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    # Генерируем токен
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, 
            role=user.role,
            login=user.login,
            username=user.username,
            full_name=user.full_name,
            expires_delta=access_token_expires,
            birth_date=user.birth_date
        ),
        "token_type": "bearer",
    }

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    # Проверка на существование email, login или username (handle)
    query = select(User).where(
        or_(
            User.email == user_in.email, 
            User.login == user_in.login,
            User.username == user_in.username
        )
    )
    result = await db.execute(query)
    existing_user = result.scalars().first()
    
    if existing_user:
        if existing_user.email == user_in.email:
            detail = "User with this email already registered"
        elif existing_user.login == user_in.login:
            detail = "Login already taken"
        else:
            detail = "Username (handle) already taken"
            
        raise HTTPException(
            status_code=400,
            detail=detail,
        )
    
    # Создание
    user = User(
        email=user_in.email,
        login=user_in.login,
        username=user_in.username,
        full_name=user_in.full_name,
        birth_date=user_in.birth_date,
        password_hash=security.get_password_hash(user_in.password),
        role="user"
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
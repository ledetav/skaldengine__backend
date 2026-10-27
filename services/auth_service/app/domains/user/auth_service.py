"""Сервис аутентификации, верификации учетных данных и регистрации."""

from datetime import timedelta
from typing import Optional, Dict
from shared.base.service import BaseService
from .repository import UserRepository
from .models import User
from app.core.security import verify_password, create_access_token, get_password_hash, TokenPayload
from app.core.config import settings
from app.domains.user.schemas import UserCreate, UserResponse, Token


class AuthService(BaseService[UserRepository]):
    """Сервис аутентификации и регистрации пользователей."""

    async def authenticate(self, identifier: str, password: str) -> Optional[Dict]:
        """Аутентифицирует пользователя по логину/email и паролю.

        Args:
            identifier: Email или логин пользователя.
            password: Введённый пароль.

        Returns:
            Словарь с токеном доступа или None, если проверка не пройдена.
        """
        user = await self.repository.get_by_email_or_login(identifier)
        if not user or not verify_password(password, user.password_hash):
            return None
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = TokenPayload(
            subject=user.id,
            role=user.role,
            login=user.login,
            username=user.username,
            full_name=user.full_name,
            birth_date=user.birth_date
        )
        token = create_access_token(
            payload=payload,
            expires_delta=access_token_expires
        )
        return {
            "access_token": token,
            "token_type": "bearer",
        }

    async def register(self, user_in: UserCreate) -> User:
        """Регистрирует нового пользователя в системе.

        Args:
            user_in: Данные для создания пользователя.

        Returns:
            Созданный объект модели User.

        Raises:
            ValueError: Если email, login или username уже зарегистрированы.
        """
        # Проверяем, существует ли уже пользователь с такими данными
        existing_user = await self.repository.check_existence(
            email=user_in.email,
            login=user_in.login,
            username=user_in.username
        )
        if existing_user:
            if existing_user.email == user_in.email:
                raise ValueError("Пользователь с таким email уже зарегистрирован")
            elif existing_user.login == user_in.login:
                raise ValueError("Логин уже занят")
            else:
                raise ValueError("Имя пользователя (@handle) уже занято")

        user_data = {
            "email": user_in.email,
            "login": user_in.login,
            "username": user_in.username,
            "full_name": user_in.full_name,
            "birth_date": user_in.birth_date,
            "password_hash": get_password_hash(user_in.password),
            "role": "user",
            "avatar_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed={user_in.username}"
        }
        return await self.repository.create(obj_in=user_data)


from datetime import timedelta
from typing import Optional, Dict
from shared.base.service import BaseService
from .repository import UserRepository
from .models import User
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.config import settings
from app.domains.user.schemas import UserCreate, UserResponse, Token

class AuthService(BaseService[UserRepository]):
    async def authenticate(self, identifier: str, password: str) -> Optional[Dict]:
        user = await self.repository.get_by_email_or_login(identifier)
        if not user or not verify_password(password, user.password_hash):
            return None
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token = create_access_token(
            user.id,
            role=user.role,
            login=user.login,
            username=user.username,
            full_name=user.full_name,
            expires_delta=access_token_expires,
            birth_date=user.birth_date,
            polza_api_key=user.polza_api_key
        )
        return {
            "access_token": token,
            "token_type": "bearer",
        }

    async def register(self, user_in: UserCreate) -> User:
        # Check if user exists
        existing_user = await self.repository.check_existence(
            email=user_in.email,
            login=user_in.login,
            username=user_in.username
        )
        if existing_user:
            if existing_user.email == user_in.email:
                raise ValueError("User with this email already registered")
            elif existing_user.login == user_in.login:
                raise ValueError("Login already taken")
            else:
                raise ValueError("Username (handle) already taken")

        user_data = {
            "email": user_in.email,
            "login": user_in.login,
            "username": user_in.username,
            "full_name": user_in.full_name,
            "birth_date": user_in.birth_date,
            "password_hash": get_password_hash(user_in.password),
            "role": "user",
            "polza_api_key": user_in.polza_api_key
        }
        return await self.repository.create(obj_in=user_data)

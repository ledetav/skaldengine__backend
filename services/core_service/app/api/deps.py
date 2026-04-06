from typing import AsyncGenerator
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.config import settings
from app.db.base import AsyncSessionLocal

from datetime import date

class CurrentUser(BaseModel):
    id: UUID
    role: str = "user"
    username: str | None = None
    full_name: str | None = None
    birth_date: date | None = None

# Используем HTTPBearer вместо OAuth2PasswordBearer.
# Это создаст в Swagger поле для ручной вставки токена, вместо формы логина.
security = HTTPBearer()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(token_auth: HTTPAuthorizationCredentials = Depends(security)) -> CurrentUser:
    # HTTPBearer возвращает объект, сам токен лежит в .credentials
    token = token_auth.credentials
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = payload.get("sub")
        if token_data is None:
             raise HTTPException(status_code=403, detail="Invalid token")
        
        user_id = UUID(token_data)
        role = payload.get("role", "user")
        username = payload.get("username")
        full_name = payload.get("full_name")
        
        # Parse birth_date
        birth_date_str = payload.get("birth_date")
        birth_date_val = None
        if birth_date_str:
            try:
                birth_date_val = date.fromisoformat(birth_date_str)
            except ValueError:
                pass

        return CurrentUser(
            id=user_id, 
            role=role, 
            username=username, 
            full_name=full_name, 
            birth_date=birth_date_val
        )
        
    except (JWTError, ValueError): 
        raise HTTPException(status_code=403, detail="Could not validate credentials")

def verify_admin_role(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    if current_user.role not in ["admin", "moderator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges (requires admin or moderator role)"
        )
    return current_user
    
# Alias for compatibility with some endpoints
get_current_active_superuser = verify_admin_role
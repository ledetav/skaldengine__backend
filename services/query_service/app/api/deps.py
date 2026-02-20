from typing import AsyncGenerator
from uuid import UUID
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.config import settings
from app.db.base import AsyncSessionLocal

class CurrentUser(BaseModel):
    id: UUID

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
        
        user_id = UUID(token_data)
        return CurrentUser(id=user_id)
    except (JWTError, ValueError): 
        raise HTTPException(status_code=403, detail="Could not validate credentials")
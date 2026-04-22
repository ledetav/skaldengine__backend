from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Union
from jose import jwt
import bcrypt
from app.core.config import settings

@dataclass
class TokenPayload:
    subject: Union[str, Any]
    role: str = "user"
    login: str | None = None
    username: str | None = None
    full_name: str | None = None
    birth_date: Union[datetime, Any] = None
    polza_api_key: str | None = None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(
    payload: TokenPayload,
    expires_delta: timedelta | None = None
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(payload.subject), "role": payload.role}
    if payload.login:
        to_encode["login"] = payload.login
    if payload.username:
        to_encode["username"] = payload.username
    if payload.full_name:
        to_encode["full_name"] = payload.full_name
    if payload.birth_date:
        to_encode["birth_date"] = payload.birth_date.isoformat() if hasattr(payload.birth_date, 'isoformat') else str(payload.birth_date)
    if payload.polza_api_key:
        to_encode["polza_api_key"] = payload.polza_api_key
        
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

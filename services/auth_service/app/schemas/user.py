from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import date, datetime


class UserBase(BaseModel):
    email: EmailStr
    username: str
    login: str


class UserCreate(UserBase):
    password: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@example.com",
                    "username": "SuperPlayer2000",
                    "login": "super_player",
                    "password": "strongpassword123"
                }
            ]
        }
    }


class UserLogin(BaseModel):
    username: str  # OAuth2PasswordRequestForm использует username, а не email
    password: str


class UserResponse(UserBase):
    id: UUID
    role: str
    avatar_url: str | None = None
    birth_date: date | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
import re
from pydantic import BaseModel, EmailStr, field_validator
from uuid import UUID
from datetime import date, datetime


class UserBase(BaseModel):
    email: EmailStr
    login: str
    username: str
    full_name: str | None = None
    birth_date: date

    @field_validator("login")
    @classmethod
    def validate_login(cls, v: str) -> str:
        if v.strip() != v:
            raise ValueError("Login cannot have leading or trailing spaces")
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Login can only contain alphanumeric characters, hyphens, and underscores")
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if v.strip() != v:
            raise ValueError("Username cannot have leading or trailing spaces")
        if not v.startswith("@"):
            v = "@" + v
        if not re.match(r"^@[a-zA-Z0-9_-]+$", v):
            raise ValueError("Username can only contain alphanumeric characters, hyphens, and underscores")
        return v


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(not c.isalnum() for c in v):
            raise ValueError("Password must contain at least one special character")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@example.com",
                    "login": "SuperPlayer2000",
                    "username": "@Skaldik",
                    "full_name": "Ivan Ivanov",
                    "password": "StrongPassword123!",
                    "birth_date": "1995-04-03"
                }
            ]
        }
    }


class UserLogin(BaseModel):
    login: str  # OAuth2PasswordRequestForm использует username, а не email
    password: str


class LoginUpdate(BaseModel):
    new_login: str

    @field_validator("new_login")
    @classmethod
    def validate_login(cls, v: str) -> str:
        return UserBase.validate_login(v)


class UsernameUpdate(BaseModel):
    new_username: str

    @field_validator("new_username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        return UserBase.validate_username(v)


class EmailUpdate(BaseModel):
    new_email: EmailStr


class FullNameUpdate(BaseModel):
    full_name: str | None = None


class ProfileUpdate(BaseModel):
    avatar_url: str | None = None
    cover_url: str | None = None


class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return UserCreate.validate_password(v)


class UserResponse(UserBase):
    id: UUID
    role: str
    avatar_url: str | None = None
    cover_url: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
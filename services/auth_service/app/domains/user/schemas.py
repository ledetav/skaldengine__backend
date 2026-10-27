"""Pydantic-схемы данных для пользователей и аутентификации."""

import re
from typing import Literal
from pydantic import BaseModel, EmailStr, field_validator, Field
from uuid import UUID
from datetime import date, datetime


class UserBase(BaseModel):
    """Базовая схема с общими полями пользователя."""

    email: EmailStr = Field(..., description="Адрес электронной почты")
    login: str = Field(..., description="Уникальный логин для входа")
    username: str = Field(..., description="Публичный никнейм/хэндл (@handle)")
    full_name: str | None = Field(default=None, max_length=200, description="Полное имя")
    about: str | None = Field(default=None, max_length=500, description="Информация о себе")
    birth_date: date = Field(..., description="Дата рождения")

    @field_validator("login")
    @classmethod
    def validate_login(cls, v: str) -> str:
        """Валидация формата логина."""
        if v.strip() != v:
            raise ValueError("Логин не должен содержать начальные или конечные пробелы")
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Логин может содержать только латинские буквы, цифры, дефисы и знаки подчеркивания")
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Валидация публичного никнейма."""
        if v.strip() != v:
            raise ValueError("Имя пользователя не должно содержать начальные или конечные пробелы")
        if v.startswith("@"):
            v = v[1:]
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Имя пользователя может содержать только латинские буквы, цифры, дефисы и знаки подчеркивания")
        return v


class UserCreate(UserBase):
    """Схема для регистрации нового пользователя."""

    password: str = Field(..., description="Пароль пользователя")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Валидация сложности пароля."""
        if len(v) < 8:
            raise ValueError("Пароль должен содержать не менее 8 символов")
        if not any(c.isdigit() for c in v):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        if not any(c.isupper() for c in v):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
        if not any(not c.isalnum() for c in v):
            raise ValueError("Пароль должен содержать хотя бы один специальный символ")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@example.com",
                    "login": "SuperPlayer2000",
                    "username": "Skaldik",
                    "full_name": "Иван Иванов",
                    "password": "StrongPassword123!",
                    "birth_date": "1995-04-03"
                }
            ]
        }
    }


class UserLogin(BaseModel):
    """Схема для аутентификации пользователя."""

    login: str = Field(..., description="Логин или username")
    password: str = Field(..., description="Пароль")


class LoginUpdate(BaseModel):
    """Схема для обновления логина."""

    new_login: str = Field(..., description="Новый уникальный логин")

    @field_validator("new_login")
    @classmethod
    def validate_login(cls, v: str) -> str:
        """Валидирует обновляемый логин по общим правилам UserBase."""
        return UserBase.validate_login(v)


class UsernameUpdate(BaseModel):
    """Схема для обновления публичного никнейма."""

    new_username: str = Field(..., description="Новое публичное имя пользователя")

    @field_validator("new_username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Валидирует обновляемый никнейм по общим правилам UserBase."""
        return UserBase.validate_username(v)


class EmailUpdate(BaseModel):
    """Схема для обновления адреса электронной почты."""

    new_email: EmailStr = Field(..., description="Новый email адрес")


class FullNameUpdate(BaseModel):
    """Схема для обновления полного имени."""

    full_name: str | None = Field(default=None, max_length=200, description="Полное имя")


class ProfileUpdate(BaseModel):
    """Схема для обновления данных профиля (аватар, обложка, описание)."""

    avatar_url: str | None = Field(None, description="URL аватара")
    cover_url: str | None = Field(None, description="URL обложки профиля")
    about: str | None = Field(default=None, max_length=500, description="Информация о себе")


class UserUpdate(BaseModel):
    """Схема для комплексного обновления данных пользователя."""

    email: EmailStr | None = None
    login: str | None = None
    username: str | None = None
    full_name: str | None = Field(default=None, max_length=200)
    about: str | None = Field(default=None, max_length=500)
    avatar_url: str | None = None
    cover_url: str | None = None

    @field_validator("login")
    @classmethod
    def validate_login(cls, v: str | None) -> str | None:
        """Валидирует логин при частичном обновлении данных пользователя."""
        if v is None:
            return v
        return UserBase.validate_login(v)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str | None) -> str | None:
        """Валидирует никнейм при частичном обновлении данных пользователя."""
        if v is None:
            return v
        return UserBase.validate_username(v)


class PasswordUpdate(BaseModel):
    """Схема для смены пароля."""

    old_password: str = Field(..., description="Текущий пароль")
    new_password: str = Field(..., description="Новый пароль")

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Валидирует сложность и длину нового пароля."""
        return UserCreate.validate_password(v)


class RoleUpdate(BaseModel):
    """Схема для назначения роли пользователю."""

    role: Literal["user", "moderator", "admin"] = Field(..., description="Новая роль пользователя")


class UserResponse(UserBase):
    """Схема полного ответа с данными пользователя."""

    id: UUID
    role: str
    avatar_url: str | None = None
    cover_url: str | None = None
    created_at: datetime

    class Config:
        """Конфигурация сериализации ORM-модели SQLAlchemy в схему Pydantic."""
        from_attributes = True


class PublicProfileResponse(BaseModel):
    """Схема публичного профиля пользователя."""

    id: UUID
    username: str
    full_name: str | None = None
    avatar_url: str | None = None
    cover_url: str | None = None
    about: str | None = None
    role: str
    created_at: datetime

    class Config:
        """Конфигурация сериализации ORM-модели SQLAlchemy в схему Pydantic."""
        from_attributes = True


class Token(BaseModel):
    """Схема возвращаемого JWT-токена доступа."""

    access_token: str = Field(..., description="JWT access токен")
    token_type: str = Field(default="bearer", description="Тип токена")

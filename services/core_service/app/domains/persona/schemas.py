"""Pydantic-схемы данных для персон пользователя и статистики."""

from pydantic import BaseModel, field_validator, Field, ConfigDict
from uuid import UUID
from datetime import datetime


class UserPersonaBase(BaseModel):
    """Базовая схема персоны пользователя с игровыми характеристиками."""

    name: str = Field(..., max_length=200, description="Имя игрового персонажа")
    description: str | None = Field(default=None, max_length=500, description="Краткое описание")
    avatar_url: str | None = Field(None, description="URL аватара персоны")
    age: str | None = Field(default=None, max_length=100, description="Возраст")
    appearance: str | None = Field(default=None, max_length=2000, description="Внешность")
    personality: str | None = Field(default=None, max_length=2000, description="Характер и особенности личности")
    gender: str | None = Field(default=None, max_length=100, description="Пол")
    facts: str | None = Field(default=None, max_length=2000, description="Факты, биография и предыстория")

    @field_validator("age", mode="before")
    @classmethod
    def age_to_str(cls, v):
        """Приводит возраст к строковому типу данных."""
        if v is None:
            return None
        return str(v)


class UserPersonaCreate(UserPersonaBase):
    """Схема для создания новой персоны."""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Арагорн",
                    "description": "Следопыт Севера и наследник престола.",
                    "avatar_url": "https://example.com/aragor.jpg",
                    "age": "35",
                    "appearance": "Высокий, темноволосый, со шрамом на лице",
                    "personality": "Стойкий, сдержанный и храбрый",
                    "gender": "мужской",
                    "facts": "Изгнанник со своей родины"
                }
            ]
        }
    }


class UserPersonaUpdate(BaseModel):
    """Схема для обновления существующей персоны."""

    name: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    avatar_url: str | None = None
    age: str | None = Field(default=None, max_length=100)
    appearance: str | None = Field(default=None, max_length=2000)
    personality: str | None = Field(default=None, max_length=2000)
    gender: str | None = Field(default=None, max_length=100)
    facts: str | None = Field(default=None, max_length=2000)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Арагорн Король",
                    "description": "Коронованный правитель Гондора.",
                    "avatar_url": "https://example.com/aragor_king.jpg",
                    "age": "40",
                    "appearance": "Величественный вид, седеющие волосы",
                    "personality": "Мудрый и справедливый",
                    "gender": "мужской",
                    "facts": "Вернул корону предков"
                }
            ]
        }
    }


class UserPersonaResponse(UserPersonaBase):
    """Схема ответа с полными данными персоны пользователя."""

    id: UUID
    owner_id: UUID
    lorebook_count: int = 0
    chat_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserStatistics(BaseModel):
    """Схема сводной статистики пользователя."""

    total_personas: int = Field(0, description="Общее число персон")
    total_lorebooks: int = Field(0, description="Общее число лорбуков")
    total_chats: int = Field(0, description="Общее число чатов")
    total_messages: int = Field(0, description="Общее число сообщений")


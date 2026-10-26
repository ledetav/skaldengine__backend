"""
Pydantic-схемы для работы со сценариями (Scenario).
"""

from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class ScenarioBase(BaseModel):
    """Базовые атрибуты сценария."""
    title: str = Field(..., max_length=200, description="Название сценария")
    location: str | None = Field(default=None, max_length=200, description="Локация действия")
    description: str = Field(..., max_length=500, description="Публичное описание завязки")
    start_point: str = Field(..., max_length=500, description="Начальная точка сюжета (точка А)")
    end_point: str = Field(..., max_length=500, description="Целевая точка сюжета (точка Б)")
    character_id: UUID | None = Field(default=None, description="Идентификатор связанного персонажа")


class ScenarioCreate(ScenarioBase):
    """Схема создания сценария."""
    internal_description: str | None = Field(
        default=None,
        max_length=1000,
        description="Внутреннее описание/инструкции для ИИ (скрыто от обычных пользователей)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Ограбление века",
                    "description": "Проникнуть в хранилище и похитить алмаз.",
                    "internal_description": "Хранилище заминировано газом. Алмаз поддельный, если не нажат секретный рычаг.",
                    "start_point": "У здания банка в полночь.",
                    "end_point": "Побег на автомобиле с добычей.",
                    "character_id": "123e4567-e89b-12d3-a456-426614174000"
                }
            ]
        }
    }


class ScenarioUpdate(BaseModel):
    """Схема частичного обновления данных сценария."""
    title: str | None = Field(default=None, max_length=200, description="Название сценария")
    location: str | None = Field(default=None, max_length=200, description="Локация действия")
    description: str | None = Field(default=None, max_length=500, description="Публичное описание")
    internal_description: str | None = Field(default=None, max_length=1000, description="Скрытые инструкции для ИИ")
    start_point: str | None = Field(default=None, max_length=500, description="Точка А")
    end_point: str | None = Field(default=None, max_length=500, description="Точка Б")
    character_id: UUID | None = Field(default=None, description="ID персонажа")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Ограбление (сложный режим)",
                    "description": "Проникнуть в хранилище без шума.",
                    "start_point": "Инфильтрация через крышу.",
                    "end_point": "Спрятать добычу незамеченным."
                }
            ]
        }
    }


class ScenarioShort(BaseModel):
    """Краткое представление сценария для списков."""
    id: UUID
    character_id: UUID | None = None
    title: str
    location: str | None = None
    description: str
    chats_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class Scenario(ScenarioBase):
    """Публичная схема сценария с количеством активных сессий."""
    id: UUID
    chats_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ScenarioFull(Scenario):
    """Полная схема сценария (включает внутренние инструкции для ИИ)."""
    internal_description: str | None = Field(default=None, max_length=1000)


# Псевдонимы схем ответов API
ScenarioResponse = Scenario
ScenarioAdminResponse = ScenarioFull


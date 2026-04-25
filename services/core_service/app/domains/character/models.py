import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Text, Boolean, Index, ForeignKey, Column, Table, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


# Таблица для связи "Многие ко многим" между персонажами и лорбуками
character_lorebook_association = Table(
    "character_lorebook_association",
    Base.metadata,
    Column("character_id", ForeignKey("characters.id", ondelete="CASCADE"), primary_key=True),
    Column("lorebook_id", ForeignKey("lorebooks.id", ondelete="CASCADE"), primary_key=True),
)

class CharacterType(str, enum.Enum):
    FANDOM = "fandom"
    ORIGINAL = "original"

class Character(Base):
    """
    AI Персонажи (боты). Создаются пользователями или администраторами.
    """
    __tablename__ = "characters"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Создатель персонажа (raw UUID — владелец в auth_db)
    creator_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)

    # Тип персонажа (Requirement 2026-04-25: FANDOM or ORIGINAL)
    type: Mapped[CharacterType] = mapped_column(Enum(CharacterType), default=CharacterType.FANDOM, index=True)

    # Публичная информация (каталог)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)   # Краткое публичное описание
    fandom: Mapped[str | None] = mapped_column(String, index=True, nullable=True)  # Вселенная/фандом

    # Визуал
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)
    card_image_url: Mapped[str | None] = mapped_column(String, nullable=True)

    # Промптинг (базовые компоненты для системного промпта)
    appearance: Mapped[str | None] = mapped_column(Text, nullable=True)
    personality: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Статистика
    total_chats_count: Mapped[int] = mapped_column(default=0)
    monthly_chats_count: Mapped[int] = mapped_column(default=0) # Статистика за прошедший календарный месяц
    scenario_chats_count: Mapped[int] = mapped_column(default=0)

    # Среда и контент
    gender: Mapped[str | None] = mapped_column(String(50), nullable=True) # мужской, женский, другой
    nsfw_allowed: Mapped[bool] = mapped_column(Boolean, default=True)

    # Доступность
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Связи
    attributes: Mapped[list["CharacterAttribute"]] = relationship(
        "CharacterAttribute", back_populates="character", cascade="all, delete-orphan"
    )
    # Многие ко многим для гибкого управления лорбуками (фандомные + персональные)
    lorebooks: Mapped[list["Lorebook"]] = relationship(
        "Lorebook", 
        secondary=character_lorebook_association,
        back_populates="characters"
    )
    scenarios: Mapped[list["Scenario"]] = relationship(
        "Scenario", back_populates="character"
    )
    chats: Mapped[list["Chat"]] = relationship(
        "Chat", back_populates="character"
    )
import uuid
from sqlalchemy import String, Text, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Character(Base):
    """
    AI Персонажи (боты). Создаются пользователями или администраторами.
    """
    __tablename__ = "characters"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Создатель персонажа (raw UUID — владелец в auth_db)
    creator_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)

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

    # Доступность
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)

    # Связи
    attributes: Mapped[list["CharacterAttribute"]] = relationship(
        "CharacterAttribute", back_populates="character", cascade="all, delete-orphan"
    )
    lorebooks: Mapped[list["Lorebook"]] = relationship(
        "Lorebook", back_populates="character", cascade="all, delete-orphan"
    )
    scenarios: Mapped[list["Scenario"]] = relationship(
        "Scenario", back_populates="character"
    )
    chats: Mapped[list["Chat"]] = relationship(
        "Chat", back_populates="character"
    )
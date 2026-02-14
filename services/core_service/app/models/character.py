import uuid
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class Character(Base):
    """
    AI Персонажи (Боты).
    """
    __tablename__ = "characters"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String)
    
    # Визуал
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)
    
    # Промптинг (Разбиваем на компоненты)
    appearance: Mapped[str] = mapped_column(Text)       # Внешность
    personality_traits: Mapped[str] = mapped_column(Text) # Характер
    speech_style: Mapped[str] = mapped_column(Text)       # Стиль речи
    inner_world: Mapped[str | None] = mapped_column(Text, nullable=True) # Скрытые мысли
    behavioral_cues: Mapped[str | None] = mapped_column(Text, nullable=True) # Поведение

    # Связи
    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="ai_character")
    lore_items: Mapped[list["LoreItem"]] = relationship("LoreItem", back_populates="character", cascade="all, delete-orphan")
    scenarios: Mapped[list["Scenario"]] = relationship("Scenario", back_populates="owner_character")
import uuid
from sqlalchemy import String, Text, Integer, ForeignKey, ARRAY, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.db.base import Base


import enum
from sqlalchemy import Enum

class LorebookType(str, enum.Enum):
    FANDOM = "fandom"
    CHARACTER = "character"
    PERSONA = "persona"

class Lorebook(Base):
    """
    Справочник мира — контейнер для лор-записей.
    Может быть привязан к персонажу или к фандому целиком.
    """
    __tablename__ = "lorebooks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    type: Mapped[LorebookType] = mapped_column(Enum(LorebookType), default=LorebookType.FANDOM, index=True)

    # Привязка к персонажу (опционально — для персонального лора)
    character_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"), nullable=True, index=True
    )
    
    # Привязка к персоне пользователя (опционально — для биографии игрока)
    user_persona_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("user_personas.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Фандом (для подтягивания ко всем персонажам вселенной)
    fandom: Mapped[str | None] = mapped_column(String, index=True, nullable=True)

    name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Связи
    characters: Mapped[list["Character"]] = relationship(
        "Character", 
        secondary="character_lorebook_association",
        back_populates="lorebooks"
    )
    user_persona: Mapped["UserPersona | None"] = relationship("UserPersona")

    entries: Mapped[list["LorebookEntry"]] = relationship(
        "LorebookEntry", back_populates="lorebook", cascade="all, delete-orphan"
    )


from pgvector.sqlalchemy import Vector

class LorebookEntry(Base):
    """
    Лор-запись — конкретный факт мира с ключевыми словами для триггера.
    keywords хранится как TEXT[] (PostgreSQL array) с GIN-индексом для быстрого поиска.
    """
    __tablename__ = "lorebook_entries"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    lorebook_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lorebooks.id", ondelete="CASCADE")
    )

    # Категория факта: fact, appearance, mindset, speech, inventory, secret
    category: Mapped[str] = mapped_column(String, index=True, default="fact")
    
    # Если True — факт всегда подтягивается в промпт (для ключевых черт)
    is_always_included: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    # TEXT[] — лексические триггеры вставки ["меч", "магия"]
    keywords: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)

    content: Mapped[str] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(Integer, default=0)

    # Эмбеддинг для семантического поиска (позволяет найти "паука" по слову "арахнид")
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Связи
    lorebook: Mapped["Lorebook"] = relationship("Lorebook", back_populates="entries")


# GIN-индекс для быстрого поиска по keywords (операции @>, &&, <@)
_idx_lorebook_entry_keywords = Index(
    "ix_lorebook_entries_keywords",
    LorebookEntry.keywords,
    postgresql_using="gin",
)

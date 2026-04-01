import uuid
from sqlalchemy import String, Text, Integer, ForeignKey, ARRAY, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Lorebook(Base):
    """
    Справочник мира — контейнер для лор-записей.
    Может быть привязан к персонажу или к фандому целиком.
    """
    __tablename__ = "lorebooks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Привязка к персонажу (опционально — для персонального лора)
    character_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Фандом (для подтягивания ко всем персонажам вселенной)
    fandom: Mapped[str | None] = mapped_column(String, index=True, nullable=True)

    name: Mapped[str] = mapped_column(String)

    # Связи
    character: Mapped["Character | None"] = relationship("Character", back_populates="lorebooks")
    entries: Mapped[list["LorebookEntry"]] = relationship(
        "LorebookEntry", back_populates="lorebook", cascade="all, delete-orphan"
    )


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

    # TEXT[] — лексические триггеры вставки ["меч", "магия"]
    keywords: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)

    content: Mapped[str] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(Integer, default=0)

    # Связи
    lorebook: Mapped["Lorebook"] = relationship("Lorebook", back_populates="entries")


# GIN-индекс для быстрого поиска по keywords (операции @>, &&, <@)
_idx_lorebook_entry_keywords = Index(
    "ix_lorebook_entries_keywords",
    LorebookEntry.keywords,
    postgresql_using="gin",
)

import uuid
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Scenario(Base):
    """
    Шаблоны сценариев — описывают точку А и точку Б для конкретного персонажа.
    """
    __tablename__ = "scenarios"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Персонаж-«хозяин» сценария
    character_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("characters.id", ondelete="SET NULL"), nullable=True
    )

    title: Mapped[str] = mapped_column(String)
    location: Mapped[str | None] = mapped_column(String, nullable=True) # Добавлено для Блока 9
    description: Mapped[str] = mapped_column(Text)  # Публичное описание завязки

    start_point: Mapped[str] = mapped_column(Text)  # Точка А
    end_point: Mapped[str] = mapped_column(Text)    # Точка Б

    # Связи
    character: Mapped["Character | None"] = relationship("Character", back_populates="scenarios")
    chats: Mapped[list["Chat"]] = relationship("Chat", back_populates="scenario")
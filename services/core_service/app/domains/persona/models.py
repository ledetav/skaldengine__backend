import uuid
from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.base import Base


class UserPersona(Base):
    """
    Персоны/Роли пользователя — игровые профили для разных историй.
    owner_id — raw UUID из auth_db (без FK constraint).
    """
    __tablename__ = "user_personas"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column()  # Raw UUID, no FK (cross-DB)

    # Основные поля
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(Text, nullable=True) # Краткое описание
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)

    # Игровые характеристики персоны
    age: Mapped[str | None] = mapped_column(String(50), nullable=True)
    appearance: Mapped[str | None] = mapped_column(Text, nullable=True)
    personality: Mapped[str | None] = mapped_column(Text, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(50), nullable=True)  # мужской, женский, другой
    facts: Mapped[str | None] = mapped_column(Text, nullable=True)  # Лор, предыстория, род деятельности

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
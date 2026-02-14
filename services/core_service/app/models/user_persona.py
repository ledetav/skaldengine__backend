import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.base import Base

class UserPersona(Base):
    """
    Пресеты пользователя.
    """
    __tablename__ = "user_personas"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column() # Raw UUID, no ForeignKey
    
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
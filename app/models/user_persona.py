import uuid
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base

class UserPersona(Base):
    """
    Пресеты пользователя (Кого он отыгрывает).
    """
    __tablename__ = "user_personas"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text) # Внешность, характер
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Связь с владельцем
    owner: Mapped["User"] = relationship("User", back_populates="personas")
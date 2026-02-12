import uuid
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

class StyleProfile(Base):
    """
    Профили стиля повествования (Промпты).
    """
    __tablename__ = "style_profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    
    prompt_instruction: Mapped[str] = mapped_column(Text)
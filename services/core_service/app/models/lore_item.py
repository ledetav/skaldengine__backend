import uuid
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class LoreItem(Base):
    """
    Элементы базы знаний персонажа (RAG Source).
    """
    __tablename__ = "lore_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    character_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("characters.id"))
    
    # Тип знания: "bio", "speech", "fact", "appearance"
    category: Mapped[str] = mapped_column(String, default="fact")
    
    content: Mapped[str] = mapped_column(Text)
    keywords: Mapped[str | None] = mapped_column(Text, nullable=True)

    character: Mapped["Character"] = relationship("Character", back_populates="lore_items")
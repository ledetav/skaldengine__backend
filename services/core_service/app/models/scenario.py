import uuid
from sqlalchemy import String, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class Scenario(Base):
    """
    Жесткие сценарии.
    """
    __tablename__ = "scenarios"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    
    # Привязка сценария к конкретному персонажу (необязательно, но логично)
    owner_character_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("characters.id"), nullable=True)

    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    
    start_point: Mapped[str] = mapped_column(Text)
    end_point: Mapped[str] = mapped_column(Text)
    
    # Список предлагаемых отношений ["Враги", "Друзья"]
    suggested_relationships: Mapped[list[str]] = mapped_column(JSON, default=list) 

    # Связи
    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="scenario")
    owner_character: Mapped["Character"] = relationship("Character", back_populates="scenarios")
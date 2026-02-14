import uuid
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.base import Base

class Session(Base):
    """
    Игровая сессия.
    Связь с users удалена.
    """
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    
    user_id: Mapped[uuid.UUID] = mapped_column() # Raw UUID
    
    character_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("characters.id"))
    persona_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_personas.id"))
    scenario_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("scenarios.id"), nullable=True)
    
    mode: Mapped[str] = mapped_column(String, default="sandbox")
    language: Mapped[str] = mapped_column(String, default="ru")
    speech_style: Mapped[str] = mapped_column(String, default="third_person")
    
    character_name_snapshot: Mapped[str] = mapped_column(String)
    persona_name_snapshot: Mapped[str] = mapped_column(String)
    relationship_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    cached_system_prompt: Mapped[str] = mapped_column(Text)
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Связи (User удален)
    ai_character = relationship("Character", back_populates="sessions")
    persona = relationship("UserPersona")
    scenario = relationship("Scenario")
    messages = relationship("Message", back_populates="session", cascade="all, delete")
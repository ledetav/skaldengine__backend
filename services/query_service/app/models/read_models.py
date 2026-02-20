import uuid
from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.base import Base

class SessionReadModel(Base):
    __tablename__ = "sessions" # Читаем из той же таблицы, которую заполняет проектор

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column()
    character_id: Mapped[uuid.UUID] = mapped_column()
    persona_id: Mapped[uuid.UUID] = mapped_column()
    scenario_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    
    mode: Mapped[str] = mapped_column(String)
    language: Mapped[str] = mapped_column(String)
    speech_style: Mapped[str] = mapped_column(String)
    
    character_name_snapshot: Mapped[str] = mapped_column(String)
    persona_name_snapshot: Mapped[str] = mapped_column(String)
    relationship_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    current_step: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

class MessageReadModel(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column()
    parent_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    
    role: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
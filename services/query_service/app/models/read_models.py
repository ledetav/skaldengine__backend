import uuid
from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, Integer, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.base import Base

class SessionReadModel(Base):
    __tablename__ = "sessions"

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

class CharacterReadModel(Base):
    __tablename__ = "characters"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)
    appearance: Mapped[str] = mapped_column(Text)
    personality_traits: Mapped[str] = mapped_column(Text)
    dialogue_style: Mapped[str] = mapped_column(Text)
    inner_world: Mapped[str | None] = mapped_column(Text, nullable=True)
    behavioral_cues: Mapped[str | None] = mapped_column(Text, nullable=True)

class ScenarioReadModel(Base):
    __tablename__ = "scenarios"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    owner_character_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    start_point: Mapped[str] = mapped_column(Text)
    end_point: Mapped[str] = mapped_column(Text)
    suggested_relationships: Mapped[list[str]] = mapped_column(JSON, default=list)

class UserPersonaReadModel(Base):
    __tablename__ = "user_personas"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[uuid.UUID] = mapped_column()
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class LoreItemReadModel(Base):
    __tablename__ = "lore_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    character_id: Mapped[uuid.UUID] = mapped_column()
    category: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    keywords: Mapped[str | None] = mapped_column(Text, nullable=True)
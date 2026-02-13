import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Text, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB  # Если PostgreSQL, иначе Text для SQLite
from datetime import datetime
from app.models.base import Base

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Связи
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    character_id = Column(String, ForeignKey("characters.id"), nullable=False)
    persona_id = Column(String, ForeignKey("user_personas.id"), nullable=False)
    scenario_id = Column(String, ForeignKey("scenarios.id"), nullable=True) # Может быть Null (Песочница)
    
    mode = Column(String, default="sandbox") # "sandbox" или "scenario"
    language = Column(String, default="ru") # "ru" или "en"
    speech_style = Column(String, default="third_person") # "first_person", "third_person"
    
    character_name_snapshot = Column(String) 
    persona_name_snapshot = Column(String)
    relationship_context = Column(Text, nullable=True)
    
    # System Instructions + Character Def + Persona Def + Scenario Intro
    cached_system_prompt = Column(Text)

    current_step = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="sessions")
    character = relationship("Character") 
    persona = relationship("UserPersona")
    scenario = relationship("Scenario")
    messages = relationship("Message", back_populates="session", cascade="all, delete")
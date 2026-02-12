import uuid
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, Integer, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base

class Session(Base):
    __tablename__ = "sessions"

    # Уникальный идентификатор сессии
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    
    # Внешние ключи (кто играет, с кем, в каком сценарии и стиле)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    ai_character_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("characters.id"))
    scenario_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("scenarios.id"), nullable=True)
    style_profile_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("style_profiles.id"), nullable=True)

    # Режим игры: "sandbox" (песочница) или "scenario" (жесткий сюжет)
    mode: Mapped[str] = mapped_column(String, default="sandbox")
    
    # Снапшоты (копии данных юзера на момент старта)
    # Это нужно, чтобы если юзер поменяет описание в профиле, старые чаты не сломались
    user_name_snapshot: Mapped[str] = mapped_column(String)
    user_desc_snapshot: Mapped[str] = mapped_column(Text)
    relationship_context: Mapped[str] = mapped_column(Text)
    
    # Динамика сюжета (создается маленькой нейросетью-супервизором)
    plot_points: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    current_plot_index: Mapped[int] = mapped_column(Integer, default=0)
    
    # Временные метки
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="sessions")
    ai_character: Mapped["Character"] = relationship("Character", back_populates="sessions")
    scenario: Mapped["Scenario"] = relationship("Scenario", back_populates="sessions")
    style_profile: Mapped["StyleProfile"] = relationship("StyleProfile")
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="session", cascade="all, delete-orphan")
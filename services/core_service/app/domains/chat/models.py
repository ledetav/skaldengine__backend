import uuid
from datetime import datetime
from sqlalchemy import String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Chat(Base):
    """
    Игровая сессия (переименована из Session в Chat по ТЗ).
    Содержит все параметры конкретного прохождения.
    user_id — raw UUID из auth_db (без FK constraint).
    """
    __tablename__ = "chats"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Участники (user_id без FK — cross-DB)
    user_id: Mapped[uuid.UUID] = mapped_column()
    user_persona_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_personas.id"))
    character_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("characters.id"))

    # Сценарий (NULL если sandbox)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mode: Mapped[str] = mapped_column(String, default="sandbox")  # "sandbox" | "scenario"
    scenario_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("scenarios.id"), nullable=True
    )

    # Настройки отношений
    is_acquainted: Mapped[bool] = mapped_column(Boolean, default=False)
    relationship_dynamic: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Настройки генерации
    language: Mapped[str] = mapped_column(String, default="ru")
    narrative_voice: Mapped[str] = mapped_column(String, default="third")  # "first" | "second" | "third"

    # Указатель на текущий активный лист дерева (последнее сообщение выбранной ветки)
    # Nullable при создании — заполняется после первого сообщения
    active_leaf_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("messages.id", use_alter=True, name="fk_chats_active_leaf_id"),
        nullable=True
    )
    
    # Опциональный лорбук персоны игрока (привязанный к сессии)
    persona_lorebook_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("lorebooks.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    # Связи
    character: Mapped["Character"] = relationship("Character", back_populates="chats")
    persona: Mapped["UserPersona"] = relationship("UserPersona")
    scenario: Mapped["Scenario | None"] = relationship("Scenario")
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="chat",
        cascade="all, delete-orphan",
        foreign_keys="Message.chat_id",
        lazy="select",
    )
    active_leaf: Mapped["Message | None"] = relationship(
        "Message",
        foreign_keys=[active_leaf_id],
        post_update=True,
    )
    checkpoints: Mapped[list["ChatCheckpoint"]] = relationship(
        "ChatCheckpoint", back_populates="chat", cascade="all, delete-orphan"
    )
    episodic_memories: Mapped[list["EpisodicMemory"]] = relationship(
        "EpisodicMemory", back_populates="chat", cascade="all, delete-orphan"
    )

from pgvector.sqlalchemy import Vector

class EpisodicMemory(Base):
    __tablename__ = "episodic_memories"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    chat_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"))
    message_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"))
    summary: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(768))

    chat: Mapped["Chat"] = relationship("Chat", back_populates="episodic_memories")
    message: Mapped["Message"] = relationship("Message", back_populates="episodic_memory")

from sqlalchemy import Integer

class ChatCheckpoint(Base):
    __tablename__ = "chat_checkpoints"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    chat_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"))
    order_num: Mapped[int] = mapped_column(Integer)
    goal_description: Mapped[str] = mapped_column(Text)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    messages_spent: Mapped[int] = mapped_column(Integer, default=0)

    chat: Mapped["Chat"] = relationship("Chat", back_populates="checkpoints")

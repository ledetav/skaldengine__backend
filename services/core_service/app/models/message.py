import uuid
from datetime import datetime
from sqlalchemy import String, Text, Boolean, ForeignKey, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Message(Base):
    """
    Сообщения чата. Поддерживает древовидную структуру (parent_id).
    """
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    chat_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"))

    # Ветвление: ссылка на родителя (NULL для корневого сообщения)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("messages.id"), nullable=True
    )

    role: Mapped[str] = mapped_column(String)  # "user" | "assistant" | "system"
    content: Mapped[str] = mapped_column(Text)

    # Внутренний монолог персонажа (скрытый от юзера тег мыслей)
    hidden_thought: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Флаги
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Связи
    chat: Mapped["Chat"] = relationship(
        "Chat",
        back_populates="messages",
        foreign_keys=[chat_id],
    )
    parent: Mapped["Message | None"] = relationship(
        "Message", remote_side="Message.id", backref="children"
    )
    episodic_memory: Mapped["EpisodicMemory | None"] = relationship(
        "EpisodicMemory", back_populates="message", uselist=False
    )


# B-Tree индекс для быстрой выборки истории чата по времени
_idx_messages_chat_created = Index(
    "ix_messages_chat_id_created_at",
    Message.chat_id,
    Message.created_at,
)
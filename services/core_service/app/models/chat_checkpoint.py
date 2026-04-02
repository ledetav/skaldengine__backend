import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Text, ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.chat import Chat

class ChatCheckpoint(Base):
    """
    Динамические точки сценария для конкретного чата.
    Генерируются супервизором при старте scenario-чата.
    Обновляются супервизором по мере прохождения.
    """
    __tablename__ = "chat_checkpoints"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    chat_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"))

    order_num: Mapped[int] = mapped_column(Integer)          # Порядковый номер (1, 2, 3...)
    goal_description: Mapped[str] = mapped_column(Text)       # Цель/событие, сгенерированное супервизором
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)  # Достиг ли сюжет этой точки
    messages_spent: Mapped[int] = mapped_column(Integer, default=0) # ТЗ Блок 10: счетчик для защиты от «застревания»

    # Связи
    chat: Mapped["Chat"] = relationship("Chat", back_populates="checkpoints")

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.base import Base

class ProcessedEvent(Base):
    """Уже обработанные события (для идемпотентности в Auth Service)"""
    __tablename__ = "processed_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    topic: Mapped[str] = mapped_column(String)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
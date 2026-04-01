import uuid
from sqlalchemy import Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.db.base import Base

# Размерность эмбеддингов gemini-embedding-001
EMBEDDING_DIM = 768


class EpisodicMemory(Base):
    """
    Эпизодическая память чата (RAG-слой на pgvector).
    Каждая запись — сжатый факт из диалога с его векторным представлением.
    Поиск по вектору: SELECT ... ORDER BY embedding <=> query_vec LIMIT k
    """
    __tablename__ = "episodic_memories"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    chat_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"))
    message_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE")
    )

    summary: Mapped[str] = mapped_column(Text)          # Сжатое изложение факта (chunk)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))  # 768-dim вектор

    # Связи
    chat: Mapped["Chat"] = relationship("Chat", back_populates="episodic_memories")
    message: Mapped["Message"] = relationship("Message", back_populates="episodic_memory")


# HNSW-индекс для приближённого поиска ближайших соседей (cosine distance)
# Создаётся вручную в миграции Alembic (SQLAlchemy не поддерживает HNSW нативно)
# Пример SQL: CREATE INDEX ix_episodic_memories_embedding_hnsw
#             ON episodic_memories USING hnsw (embedding vector_cosine_ops)
#             WITH (m = 16, ef_construction = 64);

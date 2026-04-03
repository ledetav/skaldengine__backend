import uuid
from sqlalchemy import String, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CharacterAttribute(Base):
    """
    Атрибуты и примеры речи персонажа.
    Заменяет старый LoreItem для хранения bio/speech/fact/mindset.
    Отличие от Lorebook: это внутренние данные персонажа (не лор мира).
    """
    __tablename__ = "character_attributes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    character_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"))

    # Тип атрибута: "fact", "speech_example", "mindset", "bio", "appearance_detail"
    category: Mapped[str] = mapped_column(String, index=True, default="fact")
    content: Mapped[str] = mapped_column(Text)
    
    # Ключевые слова для ситуативного срабатывания (по аналогии с Lorebook)
    from sqlalchemy.dialects.postgresql import ARRAY
    keywords: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)

    # Связи
    character: Mapped["Character"] = relationship("Character", back_populates="attributes")


# Составной индекс для быстрой выборки всех атрибутов конкретного типа по персонажу
_idx_char_attr_char_category = Index(
    "ix_character_attributes_character_id_category",
    CharacterAttribute.character_id,
    CharacterAttribute.category,
)

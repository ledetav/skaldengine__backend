# Порядок импорта важен: сначала модели без зависимостей,
# затем те, которые ссылаются на них.
# Alembic считывает метаданные через Base.metadata — все модели должны быть импортированы.

from app.db.base import Base  # noqa: F401 — нужен для Alembic env.py

# --- Независимые модели ---
from .user_persona import UserPersona  # noqa: F401
from .character import Character        # noqa: F401

# --- Зависят от Character ---
from .character_attribute import CharacterAttribute  # noqa: F401
from .lorebook import Lorebook, LorebookEntry        # noqa: F401
from .scenario import Scenario                        # noqa: F401

# --- Зависят от Character, UserPersona, Scenario ---
from .chat import Chat                  # noqa: F401

# --- Зависят от Chat ---
from .message import Message            # noqa: F401
from .chat_checkpoint import ChatCheckpoint  # noqa: F401

# --- Зависят от Chat и Message ---
from .episodic_memory import EpisodicMemory  # noqa: F401
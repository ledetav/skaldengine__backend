import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncOpenAI

from app.api.deps import CurrentUser
from app.core.config import settings
from app.domains.chat.models import Chat
from app.domains.character.models import Character
from app.domains.persona.models import UserPersona
from app.domains.scenario.models import Scenario


@dataclass
class PipelineContext:
    """Хранилище состояния сборки промпта, передаваемое между стадиями пайплайна."""
    db: AsyncSession
    chat_id: uuid.UUID
    current_user: CurrentUser
    parent_id: Optional[uuid.UUID] = None
    client: Optional[AsyncOpenAI] = None

    # Загружаемые сущности
    chat: Optional[Chat] = None
    character: Optional[Character] = None
    persona: Optional[UserPersona] = None
    scenario: Optional[Scenario] = None

    # Коллекции лора и памяти
    lore_fragments: List[str] = field(default_factory=list)
    memories: List[str] = field(default_factory=list)
    history: List[Dict[str, str]] = field(default_factory=list)

    # Атрибуты персонажа и персоны
    character_motivations: List[str] = field(default_factory=list)
    character_behavioral_cues: List[str] = field(default_factory=list)
    character_facts: List[str] = field(default_factory=list)
    persona_facts: List[str] = field(default_factory=list)

    scenario_directive: str = "None. Narrative is driven by sandbox interactions."

    # Группированные факты лорбуков (нормализованные)
    core_attributes: List[str] = field(default_factory=list)
    categorized_facts: Dict[str, List[str]] = field(default_factory=dict)

    persona_core_attributes: List[str] = field(default_factory=list)
    persona_categorized_facts: Dict[str, List[str]] = field(default_factory=dict)

    query_vector: Optional[List[float]] = None

    def __post_init__(self):
        if self.client is None:
            api_key = self.current_user.polza_api_key or settings.POLZA_API_KEY
            self.client = AsyncOpenAI(base_url="https://polza.ai/api/v1", api_key=api_key)

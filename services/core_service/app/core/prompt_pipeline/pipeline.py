"""Оркестратор пайплайна сборки системного промпта для языковых моделей."""

import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncOpenAI

from app.api.deps import CurrentUser
from app.domains.chat.models import Chat
from app.domains.character.models import Character
from app.domains.persona.models import UserPersona
from app.domains.scenario.models import Scenario
from app.domains.lorebook.models import LorebookEntry

from app.core.prompt_pipeline.context import PipelineContext
from app.core.prompt_pipeline.stages.identity_stage import IdentityStage
from app.core.prompt_pipeline.stages.lorebook_stage import LorebookStage, get_stems
from app.core.prompt_pipeline.stages.rag_stage import RAGStage
from app.core.prompt_pipeline.stages.scenario_stage import ScenarioStage
from app.core.prompt_pipeline.stages.history_stage import HistoryStage
from app.core.prompt_pipeline.stages.assembler_stage import AssemblerStage


class PromptPipeline:
    """
    Оркестратор сборки промпта для моделей ИИ.
    Делегирует выполнение 6 этапов изолированным модулям-стадиям.
    """

    def __init__(
        self,
        db: AsyncSession,
        chat_id: uuid.UUID,
        current_user: CurrentUser,
        parent_id: Optional[uuid.UUID] = None,
    ):
        """Инициализация пайплайна сборки промпта.

        Args:
            db: Сессия базы данных.
            chat_id: Идентификатор чата.
            current_user: Данные текущего пользователя.
            parent_id: Идентификатор родительского сообщения (при ветвлении).
        """
        self.context = PipelineContext(
            db=db,
            chat_id=chat_id,
            current_user=current_user,
            parent_id=parent_id,
        )


        # Стадии пайплайна
        self._identity_stage = IdentityStage()
        self._lorebook_stage = LorebookStage()
        self._rag_stage = RAGStage()
        self._scenario_stage = ScenarioStage()
        self._history_stage = HistoryStage()
        self._assembler_stage = AssemblerStage()

    # Свойства для прозрачной обратной совместимости с существующими тестами и сервисами
    @property
    def db(self) -> AsyncSession:
        return self.context.db

    @property
    def chat_id(self) -> uuid.UUID:
        return self.context.chat_id

    @property
    def current_user(self) -> CurrentUser:
        return self.context.current_user

    @property
    def parent_id(self) -> Optional[uuid.UUID]:
        return self.context.parent_id

    @property
    def client(self) -> Optional[AsyncOpenAI]:
        return self.context.client

    @property
    def chat(self) -> Optional[Chat]:
        return self.context.chat

    @chat.setter
    def chat(self, value: Optional[Chat]):
        self.context.chat = value

    @property
    def character(self) -> Optional[Character]:
        return self.context.character

    @character.setter
    def character(self, value: Optional[Character]):
        self.context.character = value

    @property
    def persona(self) -> Optional[UserPersona]:
        return self.context.persona

    @persona.setter
    def persona(self, value: Optional[UserPersona]):
        self.context.persona = value

    @property
    def scenario(self) -> Optional[Scenario]:
        return self.context.scenario

    @scenario.setter
    def scenario(self, value: Optional[Scenario]):
        self.context.scenario = value

    @property
    def lore_fragments(self) -> List[str]:
        return self.context.lore_fragments

    @property
    def memories(self) -> List[str]:
        return self.context.memories

    @property
    def history(self) -> List[Dict[str, str]]:
        return self.context.history

    @property
    def character_motivations(self) -> List[str]:
        return self.context.character_motivations

    @property
    def character_behavioral_cues(self) -> List[str]:
        return self.context.character_behavioral_cues

    @property
    def character_facts(self) -> List[str]:
        return self.context.character_facts

    @property
    def persona_facts(self) -> List[str]:
        return self.context.persona_facts

    @property
    def scenario_directive(self) -> str:
        return self.context.scenario_directive

    @scenario_directive.setter
    def scenario_directive(self, value: str):
        self.context.scenario_directive = value

    @property
    def core_attributes(self) -> List[str]:
        return self.context.core_attributes

    @property
    def categorized_facts(self) -> Dict[str, List[str]]:
        return self.context.categorized_facts

    @property
    def persona_core_attributes(self) -> List[str]:
        return self.context.persona_core_attributes

    @property
    def persona_categorized_facts(self) -> Dict[str, List[str]]:
        return self.context.persona_categorized_facts

    @property
    def query_vector(self) -> Optional[List[float]]:
        return self.context.query_vector

    @query_vector.setter
    def query_vector(self, value: Optional[List[float]]):
        self.context.query_vector = value

    async def build_payload(self, user_text: str) -> Dict[str, Any]:
        """
        Главный метод сборки. Проходит по всем 6 этапам через изолированные стадии.
        """
        await self._stage_1_identity()
        await self._stage_2_lorebook(user_text)
        await self._stage_3_rag(user_text)
        await self._stage_4_scenario()
        await self._stage_5_history()
        return await self._stage_6_assemble(user_text)

    async def _stage_1_identity(self) -> None:
        """Этап 1: Получение базовых сущностей одним запросом."""
        await self._identity_stage.process(self.context)

    async def _stage_2_lorebook(self, user_text: str) -> None:
        """Этап 2: Поиск по лорбуку с поддержкой категорий, гибридного поиска и Core-атрибутов."""
        await self._lorebook_stage.process(self.context, user_text)

    async def _stage_3_rag(self, user_text: str) -> None:
        """Этап 3: Поиск по эпизодической памяти через pgvector (reusing embedding)."""
        await self._rag_stage.process(self.context, user_text)

    async def _stage_4_scenario(self) -> None:
        """Этап 4: Получение текущей сценарной цели (Supervisor)."""
        await self._scenario_stage.process(self.context)

    async def _stage_5_history(self) -> None:
        """Этап 5: Реконструкция истории сообщений (последние 20)."""
        await self._history_stage.process(self.context)

    async def _stage_6_assemble(self, user_text: str) -> Dict[str, Any]:
        """Этап 6: Финальная сборка по структурированному шаблону."""
        return await self._assembler_stage.process(self.context, user_text)

    def _get_stems(self, text: str) -> List[str]:
        return get_stems(text)

    def _add_lore_to_collections(self, entry: LorebookEntry, is_core: bool = False) -> None:
        self._lorebook_stage._add_lore_to_collections(self.context, entry, is_core)

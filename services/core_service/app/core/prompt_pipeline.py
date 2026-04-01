import uuid
import ahocorasick
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from google import genai
from google.genai import types

from app.core.config import settings
from app.models.chat import Chat
from app.models.character import Character
from app.models.user_persona import UserPersona
from app.models.scenario import Scenario
from app.models.message import Message
from app.models.lorebook import Lorebook, LorebookEntry
from app.models.chat_checkpoint import ChatCheckpoint
from app.models.episodic_memory import EpisodicMemory
from app.core import rag


class PromptPipeline:
    """
    Оркестратор сборки промпта для Gemini.
    Реализует 6 этапов формирования Payload.
    """

    def __init__(self, db: AsyncSession, chat_id: uuid.UUID):
        self.db = db
        self.chat_id = chat_id
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        # Данные, которые будут собраны в процессе
        self.chat: Optional[Chat] = None
        self.character: Optional[Character] = None
        self.persona: Optional[UserPersona] = None
        self.scenario: Optional[Scenario] = None
        
        self.lore_fragments: List[str] = []
        self.memories: List[str] = []
        self.scenario_directive: Optional[str] = None
        self.history: List[types.Content] = []

    async def build_payload(self, user_text: str) -> Dict[str, Any]:
        """
        Главный метод сборки. Проходит по всем 6 этапам.
        """
        # Этап 1: Сборка статического ядра
        await self._stage_1_identity()

        # Этап 2: Извлечение семантической памяти (Lorebook)
        await self._stage_2_lorebook(user_text)

        # Этап 3: Извлечение эпизодической памяти (RAG)
        await self._stage_3_rag(user_text)

        # Этап 4: Инъекция сценарного супервизора
        await self._stage_4_scenario()

        # Этап 5: Реконструкция дерева истории
        await self._stage_5_history()

        # Этап 6: Финальная склейка
        return self._stage_6_assemble(user_text)

    async def _stage_1_identity(self):
        """Этап 1: Получение базовых сущностей одним запросом."""
        result = await self.db.execute(
            select(Chat).where(Chat.id == self.chat_id)
        )
        self.chat = result.scalar_one_or_none()
        if not self.chat:
            raise ValueError(f"Chat {self.chat_id} not found")

        # Загружаем связанные объекты
        self.character = await self.db.get(Character, self.chat.character_id)
        self.persona = await self.db.get(UserPersona, self.chat.user_persona_id)
        if self.chat.scenario_id:
            self.scenario = await self.db.get(Scenario, self.chat.scenario_id)

    async def _stage_2_lorebook(self, user_text: str):
        """Этап 2: Поиск ключевых слов в тексте пользователя через Aho-Corasick."""
        # 1. Получаем все лорбуки, связанные с персонажем или фандомом
        query = select(LorebookEntry).join(Lorebook).where(
            (Lorebook.character_id == self.character.id) | 
            (Lorebook.fandom == self.character.fandom)
        )
        result = await self.db.execute(query)
        entries = result.scalars().all()

        if not entries:
            return

        # 2. Инициализация Aho-Corasick для быстрого поиска
        automaton = ahocorasick.Automaton()
        keyword_to_entry = {}

        for entry in entries:
            for kw in entry.keywords:
                kw_lower = kw.lower()
                automaton.add_word(kw_lower, kw_lower)
                if kw_lower not in keyword_to_entry:
                    keyword_to_entry[kw_lower] = []
                keyword_to_entry[kw_lower].append(entry)

        automaton.make_automaton()

        # 3. Поиск совпадений
        found_keywords = set()
        for idx, original_kw in automaton.iter(user_text.lower()):
            found_keywords.add(original_kw)

        # 4. Сбор контента (с учетом приоритета)
        found_entries = []
        for kw in found_keywords:
            found_entries.extend(keyword_to_entry[kw])
        
        # Убираем дубликаты и сортируем по приоритету
        unique_entries = {e.id: e for e in found_entries}.values()
        sorted_entries = sorted(unique_entries, key=lambda x: x.priority, reverse=True)

        for entry in sorted_entries[:5]:  # Берем топ-5 фактов, чтобы не раздувать промпт
            self.lore_fragments.append(entry.content)

    async def _stage_3_rag(self, user_text: str):
        """Этап 3: Поиск по эпизодической памяти через pgvector."""
        # Генерируем эмбеддинг для запроса
        query_vector = await rag.get_query_embedding(user_text)
        
        # Поиск ближайших соседей в базе
        query = (
            select(EpisodicMemory)
            .where(EpisodicMemory.chat_id == self.chat_id)
            .order_by(EpisodicMemory.embedding.cosine_distance(query_vector))
            .limit(3)
        )
        result = await self.db.execute(query)
        memories = result.scalars().all()
        
        for m in memories:
            self.memories.append(m.summary)

    async def _stage_4_scenario(self):
        """Этап 4: Получение текущей сценарной цели."""
        if self.chat.mode != "scenario":
            return
            
        query = (
            select(ChatCheckpoint)
            .where(
                and_(
                    ChatCheckpoint.chat_id == self.chat_id,
                    ChatCheckpoint.is_completed == False
                )
            )
            .order_by(ChatCheckpoint.order_num.asc())
            .limit(1)
        )
        result = await self.db.execute(query)
        checkpoint = result.scalar_one_or_none()
        
        if checkpoint:
            self.scenario_directive = (
                f"ТЕКУЩАЯ СЦЕНАРНАЯ ЦЕЛЬ: {checkpoint.goal_description}. "
                "Незаметно направляй диалог к достижению этой цели."
            )

    async def _stage_5_history(self):
        """Этап 5: Реконструкция истории сообщений (последние N)."""
        # Начинаем с active_leaf_id и идем вверх
        current_id = self.chat.active_leaf_id
        messages = []
        limit = 20
        
        while current_id and len(messages) < limit:
            msg = await self.db.get(Message, current_id)
            if not msg:
                break
            messages.append(msg)
            current_id = msg.parent_id
            
        # Разворачиваем историю, чтобы она шла от старых к новым
        messages.reverse()
        
        for msg in messages:
            role = "user" if msg.role == "user" else "model"
            # Если это ассистент и у него есть скрытые мысли, можем передать их модели
            # В Gemini для этого можно использовать формат тегов или добавить в текст
            content_text = msg.content
            if msg.role == "assistant" and msg.hidden_thought:
                content_text = f"<thought>{msg.hidden_thought}</thought>\n{content_text}"
                
            self.history.append(
                types.Content(role=role, parts=[types.Part(text=content_text)])
            )

    def _stage_6_assemble(self, user_text: str) -> Dict[str, Any]:
        """Этап 6: Финальная склейка системной инструкции и Payload."""
        
        # 1. Сборка статических правил (можно вынести в отдельный шаблон/генератор)
        voice_map = {
            "first": "от 1-го лица (как персонаж)",
            "second": "обращаясь к пользователю во 2-м лице",
            "third": "от 3-го лица (ограниченное повествование)",
        }
        
        sys_parts = [
            f"Ты отыгрываешь роль персонажа по имени '{self.character.name}'.",
            f"[ПРАВИЛА]: Веди повествование {voice_map.get(self.chat.narrative_voice, 'от 3-го лица')}.",
            f"Язык общения: {self.chat.language}.",
            "Используй тег <thought> для записи своих внутренних размышлений перед ответом.",
            "",
            f"[ТВОЙ ПРОФИЛЬ]:\nВнешность: {self.character.appearance or 'Не указано'}\nЛичность: {self.character.personality or 'Не указано'}",
        ]
        
        if self.character.fandom:
            sys_parts.append(f"Вселенная/Фандом: {self.character.fandom}")

        sys_parts.append(f"\n[ИНФОРМАЦИЯ О СОБЕСЕДНИКЕ]:\nИмя: {self.persona.name}")
        if self.persona.appearance: sys_parts.append(f"Внешность игрока: {self.persona.appearance}")
        if self.persona.facts: sys_parts.append(f"Предыстория игрока: {self.persona.facts}")
        
        rel_context = self.chat.relationship_dynamic or ("Знакомы" if self.chat.is_acquainted else "Незнакомы")
        sys_parts.append(f"Ваши отношения: {rel_context}")

        if self.lore_fragments:
            sys_parts.append("\n[АКТИВНЫЙ ЛОР (Lorebook)]:")
            sys_parts.extend([f"- {f}" for f in self.lore_fragments])

        if self.memories:
            sys_parts.append("\n[ВОСПОМИНАНИЯ (RAG)]:")
            sys_parts.extend([f"- {m}" for m in self.memories])

        if self.scenario_directive:
            sys_parts.append(f"\n[СЦЕНАРНАЯ ДИРЕКТИВА]:\n{self.scenario_directive}")

        system_instruction = "\n".join(sys_parts)

        # Формируем Payload для Google GenAI SDK
        payload = {
            "system_instruction": system_instruction,
            "contents": self.history + [types.Content(role="user", parts=[types.Part(text=user_text)])],
            "config": types.GenerateContentConfig(
                temperature=settings.GEMINI_TEMPERATURE,
                top_p=0.95,
                max_output_tokens=settings.GEMINI_MAX_TOKENS,
                safety_settings=[
                    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_LOW_AND_ABOVE"),
                ]
            )
        }
        
        return payload

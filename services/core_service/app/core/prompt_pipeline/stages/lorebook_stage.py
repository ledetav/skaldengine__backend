import re
import ahocorasick
from typing import List, Set
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload

from app.core.config import settings
from app.core import rag
from app.domains.lorebook.models import LorebookEntry
from app.domains.chat.models import EpisodicMemory
from app.core.prompt_pipeline.context import PipelineContext
from app.core.prompt_pipeline.stages.base import PipelineStage


def get_stems(text: str) -> List[str]:
    """Упрощенное стеммирование для русского и английского: берем корни слов."""
    words = re.findall(r'[a-zа-я0-9]{3,}', text.lower())
    stems = []
    for w in words:
        if len(w) > 5:
            stems.append(w[:5])
        elif len(w) > 4:
            stems.append(w[:4])
        else:
            stems.append(w)
    return list(set(stems))


class LorebookStage(PipelineStage):
    """
    Этап 2: Извлечение семантической памяти (Lorebook).
    Поддерживает Core-атрибуты (is_always_included), гибридный поиск (Aho-Corasick + Vector)
    и проверку знакомства с персонажем (is_acquainted).
    """

    async def process(self, context: PipelineContext, user_text: str = "") -> None:
        if not context.character:
            return

        # 1. Формируем список актуальных лорбуков
        relevant_lb_ids = [lb.id for lb in context.character.lorebooks]
        if hasattr(context.chat, 'persona_lorebook_id') and context.chat.persona_lorebook_id:
            relevant_lb_ids.append(context.chat.persona_lorebook_id)

        base_query = (
            select(LorebookEntry)
            .options(joinedload(LorebookEntry.lorebook))
            .where(LorebookEntry.lorebook_id.in_(relevant_lb_ids))
        )

        # Подтягиваем Core-атрибуты (is_always_included == True)
        always_res = await context.db.execute(base_query.where(LorebookEntry.is_always_included == True))
        for entry in always_res.scalars().all():
            self._add_lore_to_collections(context, entry, is_core=True)

        # 2. Проверяем необходимость генерации query_vector
        lb_has_vectors = False
        vector_check_query = select(LorebookEntry.id).where(and_(
            LorebookEntry.lorebook_id.in_(relevant_lb_ids),
            LorebookEntry.embedding != None
        )).limit(1)
        lb_vec_res = await context.db.execute(vector_check_query)
        if lb_vec_res.scalar():
            lb_has_vectors = True

        has_episodes = False
        memo_check_query = (
            select(EpisodicMemory.id)
            .where(
                and_(
                    EpisodicMemory.chat_id == context.chat_id,
                    EpisodicMemory.summary != rag.EMPTY_FACTS_SENTINEL
                )
            )
            .limit(1)
        )
        memo_vec_res = await context.db.execute(memo_check_query)
        if memo_vec_res.scalar():
            has_episodes = True

        if lb_has_vectors or has_episodes:
            api_key = context.current_user.polza_api_key or settings.POLZA_API_KEY
            context.query_vector = await rag.get_query_embedding(user_text, api_key=api_key)

        found_entries_ids: Set[Any] = set()

        # А) Поиск по ключевым словам (Aho-Corasick)
        all_entries_res = await context.db.execute(base_query.where(LorebookEntry.is_always_included == False))
        candidates = all_entries_res.scalars().all()

        if candidates:
            automaton = ahocorasick.Automaton()
            stem_to_entries = {}
            has_keywords = False

            for entry in candidates:
                for kw in entry.keywords:
                    stems = get_stems(kw)
                    for s in stems:
                        if s not in stem_to_entries:
                            automaton.add_word(s, s)
                            stem_to_entries[s] = []
                        stem_to_entries[s].append(entry)
                        has_keywords = True

            if has_keywords:
                automaton.make_automaton()
                for _, stem in automaton.iter(user_text.lower()):
                    for entry in stem_to_entries.get(stem, []):
                        found_entries_ids.add(entry.id)

        # Б) Семантический поиск (Vector Search)
        if context.query_vector:
            distance = LorebookEntry.embedding.cosine_distance(context.query_vector)
            vector_query = (
                select(LorebookEntry)
                .where(and_(
                    LorebookEntry.lorebook_id.in_(relevant_lb_ids),
                    LorebookEntry.is_always_included == False,
                    LorebookEntry.embedding != None
                ))
                .order_by(distance.asc())
                .limit(5)
            )
            vector_res = await context.db.execute(vector_query)
            for entry in vector_res.scalars().all():
                found_entries_ids.add(entry.id)

        # Собираем все найденные (не core) записи, исключая повторы
        if found_entries_ids:
            final_res = await context.db.execute(
                select(LorebookEntry).where(LorebookEntry.id.in_(list(found_entries_ids)))
            )
            for entry in final_res.scalars().all():
                self._add_lore_to_collections(context, entry, is_core=False)

    @staticmethod
    def _add_lore_to_collections(context: PipelineContext, entry: LorebookEntry, is_core: bool = False) -> None:
        """Распределяет факты из лорбука по категориям для промпта."""
        fact_line = entry.content
        category = entry.category.lower() if entry.category else "fact"

        is_user_lore = entry.lorebook.type == "persona"

        if is_user_lore:
            # Если не знакомы - режем всё кроме Core и Appearance
            if context.chat and not context.chat.is_acquainted:
                if not is_core and category != "appearance":
                    return

            if is_core:
                context.persona_core_attributes.append(fact_line)
            else:
                if category not in context.persona_categorized_facts:
                    context.persona_categorized_facts[category] = []
                context.persona_categorized_facts[category].append(fact_line)
        else:
            if is_core:
                context.core_attributes.append(fact_line)
            else:
                if category not in context.categorized_facts:
                    context.categorized_facts[category] = []
                context.categorized_facts[category].append(fact_line)

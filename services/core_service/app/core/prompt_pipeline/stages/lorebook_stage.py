"""Этап 2 пайплайна: извлечение семантической памяти и лорбуков."""

import re
import ahocorasick
from typing import List, Set, Any
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload

from app.core import rag
from app.domains.lorebook.models import LorebookEntry
from app.core.prompt_pipeline.context import PipelineContext
from app.core.prompt_pipeline.stages.base import PipelineStage


class LorebookStage(PipelineStage):
    """
    Отвечает за подгрузку записей лорбуков (Core, Keyword, Semantic RAG)
    и распределение фактов по категориям для персонажа и персоны игрока.
    """

    def _add_lore_to_collections(
        self, context: PipelineContext, entry: LorebookEntry, is_core: bool = False
    ) -> None:
        """Распределяет факт из лорбука в нужные коллекции контекста."""
        cat = entry.category or "Lore"
        text = entry.content.strip()
        if not text:
            return

        is_persona = getattr(entry.lorebook, "user_persona_id", None) is not None

        if is_persona:
            if is_core:
                if text not in context.persona_core_attributes:
                    context.persona_core_attributes.append(text)
            else:
                context.persona_categorized_facts.setdefault(cat, [])
                if text not in context.persona_categorized_facts[cat]:
                    context.persona_categorized_facts[cat].append(text)
        else:
            if is_core:
                if text not in context.core_attributes:
                    context.core_attributes.append(text)
            else:
                context.categorized_facts.setdefault(cat, [])
                if text not in context.categorized_facts[cat]:
                    context.categorized_facts[cat].append(text)

    async def process(self, context: PipelineContext, user_text: str = "") -> None:
        """Выполняет поиск и распределение фактов лорбуков по категориям в PipelineContext."""
        if not context.character:
            return

        # 1. Формируем список актуальных лорбуков
        relevant_lb_ids = [lb.id for lb in context.character.lorebooks]
        if hasattr(context.chat, 'persona_lorebook_id') and context.chat.persona_lorebook_id:
            if context.chat.persona_lorebook_id not in relevant_lb_ids:
                relevant_lb_ids.append(context.chat.persona_lorebook_id)

        if not relevant_lb_ids:
            return

        base_query = (
            select(LorebookEntry)
            .options(joinedload(LorebookEntry.lorebook))
            .where(LorebookEntry.lorebook_id.in_(relevant_lb_ids))
        )

        # Подтягиваем Core-атрибуты (is_always_included == True)
        always_res = await context.db.execute(base_query.where(LorebookEntry.is_always_included == True))
        for entry in always_res.scalars().all():
            self._add_lore_to_collections(context, entry, is_core=True)

        # Проверяем наличие записей с эмбеддингами для оптимизации RAG
        vector_check_query = select(LorebookEntry.id).where(and_(
            LorebookEntry.lorebook_id.in_(relevant_lb_ids),
            LorebookEntry.embedding != None
        )).limit(1)
        lb_vec_res = await context.db.execute(vector_check_query)
        has_lb_vectors = lb_vec_res.first() is not None

        if has_lb_vectors and context.query_vector is None and user_text.strip():
            context.query_vector = await rag.get_query_embedding(user_text)

        # Текст для поиска по ключевым словам
        search_corpus = user_text
        if context.history:
            last_msgs = [m["content"] for m in context.history[-2:]]
            search_corpus = " ".join(last_msgs) + " " + user_text

        matched_entry_ids: Set[Any] = set()

        # А) Поиск по ключевым словам (Aho-Corasick)
        all_entries_res = await context.db.execute(base_query.where(LorebookEntry.is_always_included == False))
        candidates = all_entries_res.scalars().all()

        automaton = ahocorasick.Automaton()
        has_patterns = False
        for entry in candidates:
            if not entry.keywords:
                continue
            kw_list = [k.strip().lower() for k in entry.keywords.split(",") if k.strip()]
            for kw in kw_list:
                automaton.add_word(kw, (kw, entry))
                has_patterns = True

        if has_patterns and search_corpus.strip():
            automaton.make_automaton()
            corpus_lower = search_corpus.lower()
            for end_idx, (kw, entry) in automaton.iter(corpus_lower):
                start_idx = end_idx - len(kw) + 1
                before_ok = (start_idx == 0) or not corpus_lower[start_idx - 1].isalnum()
                after_ok = (end_idx == len(corpus_lower) - 1) or not corpus_lower[end_idx + 1].isalnum()
                if before_ok and after_ok:
                    matched_entry_ids.add(entry.id)
                    self._add_lore_to_collections(context, entry, is_core=False)

        # Б) Векторный семантический поиск
        if context.query_vector:
            distance = LorebookEntry.embedding.cosine_distance(context.query_vector)
            sem_query = (
                select(LorebookEntry, distance.label("distance"))
                .options(joinedload(LorebookEntry.lorebook))
                .where(and_(
                    LorebookEntry.lorebook_id.in_(relevant_lb_ids),
                    LorebookEntry.is_always_included == False,
                    LorebookEntry.embedding != None
                ))
                .order_by(distance.asc())
                .limit(5)
            )
            sem_res = await context.db.execute(sem_query)
            for entry, dist in sem_res.all():
                if dist is not None and dist <= 0.65 and entry.id not in matched_entry_ids:
                    matched_entry_ids.add(entry.id)
                    self._add_lore_to_collections(context, entry, is_core=False)

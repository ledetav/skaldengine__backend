"""Этап 3 пайплайна: извлечение эпизодической памяти диалога (RAG)."""

import datetime
from sqlalchemy import select, and_

from app.core.config import settings
from app.core import rag
from app.domains.chat.message_models import Message
from app.domains.chat.models import EpisodicMemory
from app.core.prompt_pipeline.context import PipelineContext
from app.core.prompt_pipeline.stages.base import PipelineStage


class RAGStage(PipelineStage):
    """
    Этап 3: Извлечение эпизодической памяти (RAG) через pgvector.
    Использует рекурсивный CTE для выборки предков в дереве сообщений,
    исключает пустые факты-сентинели и применяет гибридный скоринг с учетом давности.
    """

    async def process(self, context: PipelineContext, user_text: str = "") -> None:
        """Поиск наиболее релевантных воспоминаний и добавление их в context.memories."""
        if not context.query_vector:
            return


        ancestor_ids = []
        if context.parent_id:
            base_query = (
                select(Message.id, Message.parent_id)
                .where(Message.id == context.parent_id)
                .cte(name="message_tree", recursive=True)
            )
            recursive_query = (
                select(Message.id, Message.parent_id)
                .join(base_query, Message.id == base_query.c.parent_id)
            )
            cte = base_query.union_all(recursive_query)
            query = select(cte.c.id)
            result = await context.db.execute(query)
            ancestor_ids = list(result.scalars().all())

        if not ancestor_ids:
            return

        max_distance = getattr(settings, "POLZA_RAG_MAX_DISTANCE", 0.60)
        distance = EpisodicMemory.embedding.cosine_distance(context.query_vector)
        query = (
            select(EpisodicMemory, distance.label('distance'), Message.created_at)
            .join(Message, EpisodicMemory.message_id == Message.id)
            .where(and_(
                EpisodicMemory.chat_id == context.chat_id,
                EpisodicMemory.message_id.in_(ancestor_ids),
                EpisodicMemory.summary != rag.EMPTY_FACTS_SENTINEL,
                distance < max_distance
            ))
            .order_by(distance.asc())
            .limit(10)
        )
        result = await context.db.execute(query)
        candidates = result.all()

        if not candidates:
            return

        # Hybrid Scoring с учетом угасания памяти со временем
        FORGET_COEF = 0.0001
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        scored_candidates = []
        for mem, dist_val, created_at in candidates:
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=datetime.timezone.utc)
            age_seconds = max(0, (now_utc - created_at).total_seconds())
            score = dist_val + (age_seconds * FORGET_COEF)
            scored_candidates.append((score, mem))

        scored_candidates.sort(key=lambda x: x[0])
        best_memories = scored_candidates[:5]

        for _, m in best_memories:
            if m.summary != rag.EMPTY_FACTS_SENTINEL:
                context.memories.append(m.summary)

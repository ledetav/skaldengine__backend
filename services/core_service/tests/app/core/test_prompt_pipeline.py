"""Тесты третьего этапа пайплайна (RAGStage) по извлечению воспоминаний из pgvector.

Проверяет:
- Извлечение кандидатов воспоминаний при реалистичной дистанции косинусного расстояния (до 0.60).
- Гибридную оценку релевантности с приоритетом свежих воспоминаний по времени.
- Ранний выход из этапа при отсутствии вектора запроса пользователя.
- Фильтрацию служебных маркеров отсутствия фактов (EMPTY_FACTS_SENTINEL).
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.core.prompt_pipeline import PromptPipeline
from app.domains.chat.models import EpisodicMemory
from app.core.config import settings


@pytest.fixture
def mock_db():
    """Фикстура мока сессии базы данных с асинхронными методами execute и get."""
    db = MagicMock()
    db.execute = AsyncMock()
    db.get = AsyncMock()
    return db


@pytest.fixture
def current_user():
    """Фикстура тестового текущего пользователя."""
    user = MagicMock()
    user.id = uuid4()
    user.birth_date = None
    return user


@pytest.mark.asyncio
async def test_stage_3_rag_retrieves_candidates_at_realistic_distance(mock_db, current_user):
    """Проверка извлечения фактов памяти при реалистичной косинусной дистанции (0.42)."""
    chat_id = uuid4()
    parent_id = uuid4()

    pipeline = PromptPipeline(db=mock_db, chat_id=chat_id, current_user=current_user, parent_id=parent_id)
    pipeline.query_vector = [0.1] * 1536

    # 1. Mock ancestor CTE resolution
    cte_scalars = MagicMock()
    cte_scalars.all.return_value = [parent_id]
    cte_result = MagicMock()
    cte_result.scalars.return_value = cte_scalars

    # 2. Mock RAG search result with distance 0.42 (which was rejected by old 0.25 threshold)
    mem = MagicMock(spec=EpisodicMemory)
    mem.summary = "The hero found the obsidian blade in the cavern."
    rag_candidate = (mem, 0.42, datetime.now(timezone.utc))

    rag_result = MagicMock()
    rag_result.all.return_value = [rag_candidate]

    # Return CTE result first, then RAG query result
    mock_db.execute.side_effect = [cte_result, rag_result]

    await pipeline._stage_3_rag(user_text="Tell me about the sword")

    assert len(pipeline.memories) == 1
    assert pipeline.memories[0] == "The hero found the obsidian blade in the cavern."
    assert mock_db.execute.call_count == 2

    # Verify settings threshold was used
    assert settings.POLZA_RAG_MAX_DISTANCE == 0.60


@pytest.mark.asyncio
async def test_stage_3_rag_hybrid_scoring_prioritizes_recent_memories(mock_db, current_user):
    """Проверка гибридного скоринга: недавние воспоминания получают приоритет перед старыми."""
    chat_id = uuid4()
    parent_id = uuid4()

    pipeline = PromptPipeline(db=mock_db, chat_id=chat_id, current_user=current_user, parent_id=parent_id)
    pipeline.query_vector = [0.1] * 1536

    cte_scalars = MagicMock()
    cte_scalars.all.return_value = [parent_id]
    cte_result = MagicMock()
    cte_result.scalars.return_value = cte_scalars

    now = datetime.now(timezone.utc)
    old_time = now - timedelta(days=30)  # ~2,592,000 seconds ago

    mem_old = MagicMock(spec=EpisodicMemory)
    mem_old.summary = "Old fact with slightly better raw distance"
    # raw distance 0.35, but aged by 2.59M seconds -> score = 0.35 + 259.2 = ~259.55

    mem_recent = MagicMock(spec=EpisodicMemory)
    mem_recent.summary = "Recent fact with slightly higher raw distance"
    # raw distance 0.40, aged by 10 seconds -> score = 0.40 + 0.001 = ~0.401

    rag_result = MagicMock()
    rag_result.all.return_value = [
        (mem_old, 0.35, old_time),
        (mem_recent, 0.40, now - timedelta(seconds=10)),
    ]

    mock_db.execute.side_effect = [cte_result, rag_result]

    await pipeline._stage_3_rag(user_text="What happened recently?")

    assert len(pipeline.memories) == 2
    # The recent memory must rank FIRST despite having slightly higher raw distance
    assert pipeline.memories[0] == "Recent fact with slightly higher raw distance"
    assert pipeline.memories[1] == "Old fact with slightly better raw distance"


@pytest.mark.asyncio
async def test_stage_3_rag_exits_early_when_no_query_vector(mock_db, current_user):
    """Проверка раннего завершения этапа без обращения к БД, если вектор запроса не сформирован."""
    chat_id = uuid4()
    pipeline = PromptPipeline(db=mock_db, chat_id=chat_id, current_user=current_user)
    pipeline.query_vector = None

    await pipeline._stage_3_rag(user_text="Hello")

    assert pipeline.memories == []
    mock_db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_stage_3_rag_filters_out_empty_facts_sentinel(mock_db, current_user):
    """Проверка отфильтровывания маркера EMPTY_FACTS_SENTINEL из возвращаемых воспоминаний."""
    from app.core.rag import EMPTY_FACTS_SENTINEL

    chat_id = uuid4()
    parent_id = uuid4()

    pipeline = PromptPipeline(db=mock_db, chat_id=chat_id, current_user=current_user, parent_id=parent_id)
    pipeline.query_vector = [0.1] * 1536

    cte_scalars = MagicMock()
    cte_scalars.all.return_value = [parent_id]
    cte_result = MagicMock()
    cte_result.scalars.return_value = cte_scalars

    sentinel_mem = MagicMock(spec=EpisodicMemory)
    sentinel_mem.summary = EMPTY_FACTS_SENTINEL

    real_mem = MagicMock(spec=EpisodicMemory)
    real_mem.summary = "A genuine fact from the past."

    now = datetime.now(timezone.utc)
    rag_result = MagicMock()
    rag_result.all.return_value = [
        (sentinel_mem, 0.20, now),
        (real_mem, 0.30, now),
    ]

    mock_db.execute.side_effect = [cte_result, rag_result]

    await pipeline._stage_3_rag(user_text="What happened?")

    assert len(pipeline.memories) == 1
    assert pipeline.memories[0] == "A genuine fact from the past."
    assert EMPTY_FACTS_SENTINEL not in pipeline.memories

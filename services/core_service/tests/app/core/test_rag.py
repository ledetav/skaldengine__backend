"""Тесты модуля фоновой суммаризации скользящего окна диалога (RAG Sliding Window).

Проверяет:
- Ранний выход при короткой ветке диалога (< 12 сообщений).
- Вставку маркера EMPTY_FACTS_SENTINEL при отсутствии значимых фактов во фрагменте.
- Защиту от повторной суммаризации и зацикливания при наличии маркера в summarized_ids.
- Корректную вставку извлеченных фактов с эмбеддингами в EpisodicMemory и коммит транзакции.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.core import rag
from app.core.rag import EMPTY_FACTS_SENTINEL, process_sliding_window
from app.domains.chat.message_models import Message
from app.domains.chat.models import EpisodicMemory


@pytest.fixture
def mock_db():
    """Фикстура мока сессии базы данных для тестирования операций сохранения памяти."""
    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.add = MagicMock()
    db.rollback = AsyncMock()
    return db


def create_mock_messages(count: int, chat_id=None):
    """Создает цепочку фиктивных сообщений с указанным числом реплик.

    Args:
        count: Количество сообщений.
        chat_id: Идентификатор чата (опционально).

    Returns:
        Список связанных объектов Message.
    """
    c_id = chat_id or uuid4()
    messages = []
    parent_id = None
    for i in range(count):
        msg_id = uuid4()
        msg = Message(
            id=msg_id,
            chat_id=c_id,
            parent_id=parent_id,
            role="user" if i % 2 == 0 else "assistant",
            content=f"Message {i}"
        )
        parent_id = msg_id
        messages.append(msg)
    return messages


@pytest.mark.asyncio
async def test_process_sliding_window_early_exit_short_branch(mock_db):
    """Проверка пропуска суммаризации, если длина ветки меньше порогового размера окна."""
    chat_id = uuid4()
    last_msg_id = uuid4()

    branch = create_mock_messages(5, chat_id)
    branch_scalars = MagicMock()
    branch_scalars.all.return_value = list(reversed(branch))
    branch_result = MagicMock()
    branch_result.scalars.return_value = branch_scalars

    mock_db.execute.return_value = branch_result

    with patch("app.core.rag.AsyncOpenAI") as mock_openai_cls:
        await process_sliding_window(mock_db, chat_id, last_msg_id)
        mock_openai_cls.assert_not_called()
        mock_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_process_sliding_window_empty_facts_inserts_sentinel(mock_db):
    """Проверка записи маркера EMPTY_FACTS_SENTINEL при отсутствии фактов в вытесненных сообщениях."""
    chat_id = uuid4()
    last_msg_id = uuid4()

    # 12 messages: 6 fallen out, 6 in active window
    branch = create_mock_messages(12, chat_id)
    branch_scalars = MagicMock()
    branch_scalars.all.return_value = list(reversed(branch))
    branch_result = MagicMock()
    branch_result.scalars.return_value = branch_scalars

    # No messages previously summarized
    empty_summarized_scalars = MagicMock()
    empty_summarized_scalars.all.return_value = []
    empty_summarized_result = MagicMock()
    empty_summarized_result.scalars.return_value = empty_summarized_scalars

    mock_db.execute.side_effect = [branch_result, empty_summarized_result]

    mock_client = AsyncMock()
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps({"facts": []})
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response

    with patch("app.core.rag.AsyncOpenAI", return_value=mock_client):
        await process_sliding_window(mock_db, chat_id, last_msg_id)

        # Verify commit was called
        mock_db.commit.assert_awaited_once()

        # Verify sentinel memory was added
        assert mock_db.add.call_count == 1
        added_mem = mock_db.add.call_args[0][0]
        assert isinstance(added_mem, EpisodicMemory)
        assert added_mem.summary == EMPTY_FACTS_SENTINEL
        assert added_mem.message_id == branch[5].id  # Last message of unsummarized chunk (0..5)
        assert len(added_mem.embedding) == 1536
        assert added_mem.embedding[0] == 1.0


@pytest.mark.asyncio
async def test_process_sliding_window_prevents_loop_when_sentinel_in_summarized_ids(mock_db):
    """Проверка предотвращения повторной суммаризации чанка, если его маркер уже есть в БД."""
    chat_id = uuid4()
    last_msg_id = uuid4()

    # 12 messages: 6 fallen out, 6 in active window
    branch = create_mock_messages(12, chat_id)
    branch_scalars = MagicMock()
    branch_scalars.all.return_value = list(reversed(branch))
    branch_result = MagicMock()
    branch_result.scalars.return_value = branch_scalars

    # The 6th message was previously recorded as summarized (via sentinel or fact)
    summarized_scalars = MagicMock()
    summarized_scalars.all.return_value = [branch[5].id]
    summarized_result = MagicMock()
    summarized_result.scalars.return_value = summarized_scalars

    mock_db.execute.side_effect = [branch_result, summarized_result]

    mock_client = AsyncMock()
    with patch("app.core.rag.AsyncOpenAI", return_value=mock_client):
        await process_sliding_window(mock_db, chat_id, last_msg_id)

        # Because branch[5] in summarized_ids, unsummarized_chunk was cleared, remaining < 6
        mock_client.chat.completions.create.assert_not_called()
        mock_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_process_sliding_window_with_facts_inserts_and_commits(mock_db):
    """Проверка успешного сохранения извлеченных фактов с вычислением эмбеддинга."""
    chat_id = uuid4()
    last_msg_id = uuid4()

    branch = create_mock_messages(12, chat_id)
    branch_scalars = MagicMock()
    branch_scalars.all.return_value = list(reversed(branch))
    branch_result = MagicMock()
    branch_result.scalars.return_value = branch_scalars

    empty_summarized_scalars = MagicMock()
    empty_summarized_scalars.all.return_value = []
    empty_summarized_result = MagicMock()
    empty_summarized_result.scalars.return_value = empty_summarized_scalars

    mock_db.execute.side_effect = [branch_result, empty_summarized_result]

    mock_client = AsyncMock()
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps({"facts": ["The party agreed to travel north at dawn."]})
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response

    dummy_embed = [0.1] * 1536
    with patch("app.core.rag.AsyncOpenAI", return_value=mock_client), \
         patch("app.core.rag.get_embedding", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = dummy_embed

        await process_sliding_window(mock_db, chat_id, last_msg_id)

        mock_db.commit.assert_awaited_once()
        assert mock_db.add.call_count == 1
        added_mem = mock_db.add.call_args[0][0]
        assert added_mem.summary == "The party agreed to travel north at dawn."
        assert added_mem.message_id == branch[5].id

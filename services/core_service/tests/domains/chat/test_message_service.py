"""
Модульные тесты для сервиса обработки сообщений (MessageService).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from fastapi import BackgroundTasks

from app.domains.chat.message_service import MessageService
from app.domains.chat.message_schemas import MessageCreate
from app.domains.chat.models import Chat
from app.domains.chat.message_models import Message
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_repo():
    """Фикстура мока MessageRepository."""
    return AsyncMock()


@pytest.fixture
def message_service(mock_repo):
    """Фикстура экземпляра MessageService."""
    return MessageService(repository=mock_repo)


@pytest.mark.asyncio
@patch("app.api.endpoints.stream_utils.generate_chat_stream")
@patch("app.core.prompt_pipeline.PromptPipeline")
async def test_send_message_stream_scenario_does_not_call_director_prematurely(
    mock_pipeline_cls, mock_stream_func, message_service
):
    """Тест отправки сообщения в сценарном режиме без преждевременного вызова Режиссера."""
    chat_id = uuid4()
    user_id = uuid4()

    mock_chat = MagicMock(spec=Chat)
    mock_chat.id = chat_id
    mock_chat.user_id = user_id
    mock_chat.mode = "scenario"

    mock_db = MagicMock(spec=AsyncSession)
    mock_db.get = AsyncMock(return_value=mock_chat)
    mock_db.add = MagicMock()
    mock_db.flush = AsyncMock()
    mock_db.execute = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    # Active checkpoint query mock
    mock_cp_result = MagicMock()
    mock_cp_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_cp_result

    mock_pipeline = AsyncMock()
    mock_pipeline.build_payload = AsyncMock(return_value={"model": "test-model"})
    mock_pipeline_cls.return_value = mock_pipeline

    mock_stream_generator = MagicMock()
    mock_stream_func.return_value = mock_stream_generator

    mock_background_tasks = MagicMock(spec=BackgroundTasks)

    current_user = MagicMock()
    current_user.id = user_id

    message_in = MessageCreate(content="Hello AI, this is scenario mode.")

    result = await message_service.send_message_stream(
        chat_id=chat_id,
        current_user=current_user,
        message_in=message_in,
        background_tasks=mock_background_tasks,
        db=mock_db
    )

    # DirectorService.check_progress should NOT be added to background_tasks prematurely
    mock_background_tasks.add_task.assert_not_called()

    # Result should be the stream generator
    assert result == mock_stream_generator
    mock_stream_func.assert_called_once()

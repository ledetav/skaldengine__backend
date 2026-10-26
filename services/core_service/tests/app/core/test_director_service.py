import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.core.director_service import DirectorService
from app.domains.chat.message_models import Message
from app.domains.chat.models import ChatCheckpoint


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.add = MagicMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def mock_session_local(mock_session):
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=mock_session)
    cm.__aexit__ = AsyncMock(return_value=None)
    with patch("app.core.director_service.AsyncSessionLocal", return_value=cm):
        yield mock_session


@pytest.mark.asyncio
async def test_check_progress_with_leaf_id_branch_achieved(mock_session_local):
    chat_id = uuid4()
    leaf_id = uuid4()

    checkpoint = ChatCheckpoint(
        chat_id=chat_id,
        order_num=1,
        goal_description="Meet the mysterious informant in the alley.",
        is_completed=False,
    )

    cp_scalars = MagicMock()
    cp_scalars.first.return_value = checkpoint
    cp_result = MagicMock()
    cp_result.scalars.return_value = cp_scalars

    # Messages along the active branch
    msg1 = Message(id=uuid4(), chat_id=chat_id, role="user", content="Where should we meet?")
    msg2 = Message(id=leaf_id, chat_id=chat_id, role="assistant", content="I am waiting in the dark alley.")

    msg_scalars = MagicMock()
    # Reverse of CTE asc depth
    msg_scalars.all.return_value = [msg2, msg1]
    msg_result = MagicMock()
    msg_result.scalars.return_value = msg_scalars

    # Session execute: 1st call for checkpoint, 2nd call for CTE branch messages
    mock_session_local.execute.side_effect = [cp_result, msg_result]

    service = DirectorService(api_key="test-api-key")

    mock_llm_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps({
        "reasoning": "The informant stated they are waiting in the alley.",
        "is_achieved": True
    })
    mock_llm_response.choices = [mock_choice]

    with patch.object(service.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_llm_response

        await service.check_progress(chat_id=chat_id, leaf_id=leaf_id)

        assert checkpoint.is_completed is True
        mock_session_local.commit.assert_awaited_once()
        mock_create.assert_awaited_once()

        call_kwargs = mock_create.call_args[1]
        assert "Where should we meet?" in call_kwargs["messages"][0]["content"]
        assert "Meet the mysterious informant" in call_kwargs["messages"][0]["content"]


@pytest.mark.asyncio
async def test_check_progress_resolves_active_leaf_when_not_provided(mock_session_local):
    chat_id = uuid4()
    active_leaf_id = uuid4()

    checkpoint = ChatCheckpoint(
        chat_id=chat_id,
        order_num=1,
        goal_description="Find the hidden key.",
        is_completed=False,
    )

    cp_scalars = MagicMock()
    cp_scalars.first.return_value = checkpoint
    cp_result = MagicMock()
    cp_result.scalars.return_value = cp_scalars

    chat_leaf_result = MagicMock()
    chat_leaf_result.scalar_one_or_none.return_value = active_leaf_id

    msg1 = Message(id=active_leaf_id, chat_id=chat_id, role="assistant", content="I see a glimmer behind the stone.")
    msg_scalars = MagicMock()
    msg_scalars.all.return_value = [msg1]
    msg_result = MagicMock()
    msg_result.scalars.return_value = msg_scalars

    # 1. Checkpoint query
    # 2. Chat active_leaf_id query
    # 3. CTE messages query
    mock_session_local.execute.side_effect = [cp_result, chat_leaf_result, msg_result]

    service = DirectorService(api_key="test-api-key")

    mock_llm_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps({
        "reasoning": "Key is not yet found, only glimmer seen.",
        "is_achieved": False
    })
    mock_llm_response.choices = [mock_choice]

    with patch.object(service.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_llm_response

        await service.check_progress(chat_id=chat_id, leaf_id=None)

        assert checkpoint.is_completed is False
        mock_session_local.commit.assert_not_awaited()
        mock_create.assert_awaited_once()


@pytest.mark.asyncio
async def test_check_progress_fallback_flat_when_no_leaf(mock_session_local):
    chat_id = uuid4()

    checkpoint = ChatCheckpoint(
        chat_id=chat_id,
        order_num=1,
        goal_description="Start the journey.",
        is_completed=False,
    )

    cp_scalars = MagicMock()
    cp_scalars.first.return_value = checkpoint
    cp_result = MagicMock()
    cp_result.scalars.return_value = cp_scalars

    chat_leaf_result = MagicMock()
    chat_leaf_result.scalar_one_or_none.return_value = None

    msg1 = Message(id=uuid4(), chat_id=chat_id, role="user", content="Let us go.")
    msg_scalars = MagicMock()
    msg_scalars.all.return_value = [msg1]
    msg_result = MagicMock()
    msg_result.scalars.return_value = msg_scalars

    mock_session_local.execute.side_effect = [cp_result, chat_leaf_result, msg_result]

    service = DirectorService(api_key="test-api-key")

    mock_llm_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps({
        "reasoning": "Journey started.",
        "is_achieved": True
    })
    mock_llm_response.choices = [mock_choice]

    with patch.object(service.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_llm_response

        await service.check_progress(chat_id=chat_id, leaf_id=None)

        assert checkpoint.is_completed is True
        mock_session_local.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_check_progress_no_active_checkpoint(mock_session_local):
    chat_id = uuid4()

    cp_scalars = MagicMock()
    cp_scalars.first.return_value = None
    cp_result = MagicMock()
    cp_result.scalars.return_value = cp_scalars

    mock_session_local.execute.return_value = cp_result

    service = DirectorService(api_key="test-api-key")

    with patch.object(service.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        await service.check_progress(chat_id=chat_id)
        mock_create.assert_not_awaited()

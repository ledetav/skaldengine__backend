import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.chat.controller import ChatController
from app.domains.chat.schemas import ChatCreate, Chat
from shared.schemas.response import BaseResponse

@pytest.fixture
def mock_chat_service():
    return AsyncMock()

@pytest.fixture
def chat_controller(mock_chat_service):
    return ChatController(chat_service=mock_chat_service)

@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def mock_background_tasks():
    return MagicMock(spec=BackgroundTasks)

@pytest.fixture
def valid_chat_create():
    return ChatCreate(
        character_id=uuid.uuid4(),
        user_persona_id=uuid.uuid4(),
        scenario_id=None,
        is_acquainted=False,
        relationship_dynamic="Friends",
        language="en",
        narrative_voice="first"
    )

@pytest.fixture
def user_id():
    return uuid.uuid4()

@pytest.mark.asyncio
async def test_create_chat_success(
    chat_controller, mock_chat_service, valid_chat_create, user_id, mock_db, mock_background_tasks
):
    # Setup
    expected_chat = Chat(
        id=uuid.uuid4(),
        user_id=user_id,
        mode="sandbox",
        created_at="2023-01-01T00:00:00Z",
        **valid_chat_create.model_dump()
    )
    mock_chat_service.create_chat.return_value = expected_chat

    # Execution
    response = await chat_controller.create_chat(
        chat_in=valid_chat_create,
        user_id=user_id,
        background_tasks=mock_background_tasks,
        db=mock_db
    )

    # Verification
    mock_chat_service.create_chat.assert_awaited_once_with(
        valid_chat_create, user_id, mock_background_tasks, mock_db
    )
    assert isinstance(response, BaseResponse)
    assert response.success is True
    assert response.data == expected_chat

@pytest.mark.asyncio
async def test_create_chat_value_error(
    chat_controller, mock_chat_service, valid_chat_create, user_id, mock_db, mock_background_tasks
):
    # Setup
    error_message = "Character not found"
    mock_chat_service.create_chat.side_effect = ValueError(error_message)

    # Execution & Verification
    with pytest.raises(HTTPException) as exc_info:
        await chat_controller.create_chat(
            chat_in=valid_chat_create,
            user_id=user_id,
            background_tasks=mock_background_tasks,
            db=mock_db
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["success"] is False
    assert exc_info.value.detail["message"] == error_message

@pytest.mark.asyncio
async def test_create_chat_permission_error(
    chat_controller, mock_chat_service, valid_chat_create, user_id, mock_db, mock_background_tasks
):
    # Setup
    error_message = "You can only use your own personas"
    mock_chat_service.create_chat.side_effect = PermissionError(error_message)

    # Execution & Verification
    with pytest.raises(HTTPException) as exc_info:
        await chat_controller.create_chat(
            chat_in=valid_chat_create,
            user_id=user_id,
            background_tasks=mock_background_tasks,
            db=mock_db
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["success"] is False
    assert exc_info.value.detail["message"] == error_message

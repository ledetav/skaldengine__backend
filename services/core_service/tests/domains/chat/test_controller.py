"""
Модульные тесты для контроллера чатов (ChatController).
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException, status

from app.domains.chat.controller import ChatController
from app.domains.chat.service import ChatService
from shared.schemas.response import BaseResponse
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def chat_service_mock():
    """Фикстура мока ChatService."""
    return AsyncMock(spec=ChatService)


@pytest.fixture
def db_session_mock():
    """Фикстура мока сессии базы данных AsyncSession."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def controller(chat_service_mock):
    """Фикстура экземпляра ChatController с мок-сервисом."""
    return ChatController(chat_service=chat_service_mock)


@pytest.mark.asyncio
async def test_get_history_success(controller, chat_service_mock, db_session_mock):
    """Тест успешного получения истории сообщений чата."""
    # Arrange
    chat_id = uuid.uuid4()
    user_id = uuid.uuid4()
    mock_payload = [{"id": str(uuid.uuid4()), "content": "hello"}]
    chat_service_mock.get_history_payload.return_value = mock_payload

    # Act
    response = await controller.get_history(chat_id=chat_id, user_id=user_id, db=db_session_mock)

    # Assert
    assert isinstance(response, BaseResponse)
    assert response.success is True
    assert response.data == mock_payload
    chat_service_mock.get_history_payload.assert_called_once_with(chat_id, user_id, db_session_mock)

@pytest.mark.asyncio
async def test_get_history_value_error(controller, chat_service_mock, db_session_mock):
    """Проверка генерации HTTP 404 Not Found при возникновении ValueError при получении истории."""
    # Arrange
    chat_id = uuid.uuid4()
    user_id = uuid.uuid4()
    chat_service_mock.get_history_payload.side_effect = ValueError("Chat history not found")

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await controller.get_history(chat_id=chat_id, user_id=user_id, db=db_session_mock)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail["success"] is False
    assert exc_info.value.detail["message"] == "Chat history not found"
    chat_service_mock.get_history_payload.assert_called_once_with(chat_id, user_id, db_session_mock)

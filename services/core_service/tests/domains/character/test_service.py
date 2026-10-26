"""
Модульные тесты для сервиса персонажей (CharacterService).
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from app.domains.character.service import CharacterService
from app.domains.character.models import Character
from app.domains.character.repository import CharacterRepository

# Импорт связанных моделей для корректной настройки мапперов SQLAlchemy
from app.domains.lorebook.models import Lorebook
from app.domains.scenario.models import Scenario
from app.domains.chat.models import Chat
from app.domains.persona.models import UserPersona
from app.domains.chat.message_models import Message


@pytest.mark.asyncio
async def test_delete_character_wrong_owner():
    """Тест отклонения удаления персонажа пользователем, не являющимся владельцем."""
    # Setup
    character_id = uuid4()
    real_creator_id = uuid4()
    wrong_creator_id = uuid4()

    # Mock character returned from DB
    mock_character = Character(
        id=character_id,
        creator_id=real_creator_id,
        name="Test Character",
        description="A test character",
        fandom="Test",
        avatar_url="",
        card_image_url="",
        gender="neutral",
        nsfw_allowed=False,
    )

    # Mock Repository
    mock_repo = AsyncMock(spec=CharacterRepository)
    mock_repo.get.return_value = mock_character

    # Instantiate Service
    service = CharacterService(repository=mock_repo)

    # Mock Broadcast Manager
    with patch("app.domains.character.service.manager") as mock_manager:
        mock_manager.broadcast = AsyncMock()

        # Execute
        result = await service.delete_character(character_id=character_id, creator_id=wrong_creator_id)

        # Assert
        assert result is False
        mock_repo.get.assert_awaited_once_with(character_id)
        mock_repo.update.assert_not_called()
        mock_manager.broadcast.assert_not_called()


@pytest.mark.asyncio
async def test_delete_character_success():
    character_id = uuid4()
    creator_id = uuid4()
    lb_id = uuid4()

    mock_character = Character(
        id=character_id,
        creator_id=creator_id,
        name="Test Character",
        description="A test character",
        fandom="Test",
        avatar_url="",
        card_image_url="",
        gender="neutral",
        nsfw_allowed=False,
    )

    mock_repo = AsyncMock(spec=CharacterRepository)
    mock_repo.get.return_value = mock_character

    mock_lb_result = MagicMock()
    mock_lb_result.scalars.return_value.all.return_value = [lb_id]
    mock_repo.db = AsyncMock()
    mock_repo.db.execute.side_effect = [mock_lb_result, AsyncMock()]

    service = CharacterService(repository=mock_repo)

    with patch("app.domains.character.service.manager") as mock_manager:
        mock_manager.broadcast = AsyncMock()

        result = await service.delete_character(character_id=character_id, creator_id=creator_id)

        assert result is True
        mock_repo.get.assert_awaited_once_with(character_id)
        mock_repo.update.assert_awaited_once_with(
            db_obj=mock_character,
            obj_in={"is_deleted": True, "is_public": False}
        )
        assert mock_manager.broadcast.call_count == 2
        mock_manager.broadcast.assert_any_call({
            "type": "DELETE_LOREBOOK",
            "data": {"id": str(lb_id)}
        })
        mock_manager.broadcast.assert_any_call({
            "type": "DELETE_CHARACTER",
            "data": {"id": str(character_id)}
        })


@pytest.mark.asyncio
async def test_delete_character_not_found():
    character_id = uuid4()
    mock_repo = AsyncMock(spec=CharacterRepository)
    mock_repo.get.return_value = None

    service = CharacterService(repository=mock_repo)

    with patch("app.domains.character.service.manager") as mock_manager:
        mock_manager.broadcast = AsyncMock()

        result = await service.delete_character(character_id=character_id)

        assert result is False
        mock_repo.get.assert_awaited_once_with(character_id)
        mock_repo.update.assert_not_called()
        mock_manager.broadcast.assert_not_called()

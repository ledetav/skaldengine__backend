import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.domains.character.service import CharacterService
from app.domains.character.models import Character
from app.domains.character.repository import CharacterRepository

# Import related models to fix SQLAlchemy mapper registry errors
from app.domains.lorebook.models import Lorebook
from app.domains.character.models import Character
from app.domains.character.attribute_models import CharacterAttribute
from app.domains.scenario.models import Scenario
from app.domains.chat.models import Chat
from app.domains.persona.models import UserPersona
from app.domains.chat.message_models import Message

@pytest.mark.asyncio
async def test_delete_character_wrong_owner():
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

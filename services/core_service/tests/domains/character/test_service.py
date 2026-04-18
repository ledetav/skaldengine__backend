import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

# import needed models to resolve sqlalchemy relationship strings
import app.domains.character.attribute_models
import app.domains.lorebook.models
import app.domains.scenario.models
import app.domains.chat.models
import app.domains.persona.models
import app.domains.chat.message_models

from app.domains.character.models import Character
from app.domains.character.service import CharacterService

@pytest.mark.asyncio
async def test_get_characters():
    # Setup mock repository
    mock_repo = AsyncMock()

    # Create some dummy characters
    char1 = Character(id=uuid4(), name="Char 1")
    char2 = Character(id=uuid4(), name="Char 2")

    # Configure mock returns
    mock_repo.get_active_characters.return_value = [char1, char2]

    # We can either make get_scenarios_count / get_scenario_chats_count return a static value,
    # or return different values based on character id using a side_effect
    async def mock_get_scenarios_count(char_id):
        if char_id == char1.id:
            return 5
        return 10

    async def mock_get_scenario_chats_count(char_id):
        if char_id == char1.id:
            return 20
        return 50

    mock_repo.get_scenarios_count.side_effect = mock_get_scenarios_count
    mock_repo.get_scenario_chats_count.side_effect = mock_get_scenario_chats_count

    # Initialize service
    service = CharacterService(repository=mock_repo)

    # Call method
    characters = await service.get_characters(skip=0, limit=20)

    # Assertions
    mock_repo.get_active_characters.assert_called_once_with(0, 20)

    assert len(characters) == 2
    assert characters[0].id == char1.id
    assert getattr(characters[0], "scenarios_count") == 5
    assert getattr(characters[0], "scenario_chats_count") == 20

    assert characters[1].id == char2.id
    assert getattr(characters[1], "scenarios_count") == 10
    assert getattr(characters[1], "scenario_chats_count") == 50

@pytest.mark.asyncio
async def test_get_characters_empty():
    mock_repo = AsyncMock()
    mock_repo.get_active_characters.return_value = []

    service = CharacterService(repository=mock_repo)
    characters = await service.get_characters(skip=10, limit=5)

    mock_repo.get_active_characters.assert_called_once_with(10, 5)
    assert mock_repo.get_scenarios_count.call_count == 0
    assert mock_repo.get_scenario_chats_count.call_count == 0
    assert characters == []

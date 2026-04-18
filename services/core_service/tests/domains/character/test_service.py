import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from app.domains.character.service import CharacterService
from app.domains.character.models import Character
from app.domains.character.schemas import CharacterUpdate

@pytest.fixture
def mock_repo():
    return AsyncMock()

@pytest.fixture
def service(mock_repo):
    return CharacterService(repository=mock_repo)

@pytest.mark.asyncio
async def test_update_character_success(service, mock_repo):
    character_id = uuid4()
    creator_id = uuid4()

    mock_character = MagicMock(spec=Character)
    mock_character.creator_id = creator_id
    mock_character.id = character_id

    mock_updated_character = MagicMock(spec=Character)
    mock_updated_character.id = character_id

    mock_repo.get.return_value = mock_character
    mock_repo.update.return_value = mock_updated_character

    update_data = CharacterUpdate(name="New Name")

    with patch('app.domains.character.service.manager') as mock_manager:
        mock_manager.broadcast = AsyncMock()
        with patch.object(service, '_format_broadcast_data', return_value={"id": str(character_id)}) as mock_format:
            result = await service.update_character(character_id, update_data, creator_id)

            assert result == mock_updated_character
            mock_repo.get.assert_called_once_with(character_id)
            mock_repo.update.assert_called_once_with(db_obj=mock_character, obj_in=update_data)
            mock_format.assert_called_once_with(mock_updated_character)
            mock_manager.broadcast.assert_called_once_with({
                "type": "UPDATE_CHARACTER",
                "data": {"id": str(character_id)}
            })

@pytest.mark.asyncio
async def test_update_character_not_found(service, mock_repo):
    character_id = uuid4()
    creator_id = uuid4()

    mock_repo.get.return_value = None

    update_data = CharacterUpdate(name="New Name")

    result = await service.update_character(character_id, update_data, creator_id)

    assert result is None
    mock_repo.get.assert_called_once_with(character_id)
    mock_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_update_character_forbidden(service, mock_repo):
    character_id = uuid4()
    creator_id = uuid4()
    other_creator_id = uuid4()

    mock_character = MagicMock(spec=Character)
    mock_character.creator_id = other_creator_id
    mock_character.id = character_id

    mock_repo.get.return_value = mock_character

    update_data = CharacterUpdate(name="New Name")

    result = await service.update_character(character_id, update_data, creator_id)

    assert result is None
    mock_repo.get.assert_called_once_with(character_id)
    mock_repo.update.assert_not_called()

@pytest.mark.asyncio
async def test_update_character_without_creator_id(service, mock_repo):
    character_id = uuid4()
    original_creator_id = uuid4()

    mock_character = MagicMock(spec=Character)
    mock_character.creator_id = original_creator_id
    mock_character.id = character_id

    mock_updated_character = MagicMock(spec=Character)
    mock_updated_character.id = character_id

    mock_repo.get.return_value = mock_character
    mock_repo.update.return_value = mock_updated_character

    update_data = CharacterUpdate(name="New Name")

    with patch('app.domains.character.service.manager') as mock_manager:
        mock_manager.broadcast = AsyncMock()
        with patch.object(service, '_format_broadcast_data', return_value={"id": str(character_id)}) as mock_format:
            # Not passing creator_id
            result = await service.update_character(character_id, update_data)

            assert result == mock_updated_character
            mock_repo.get.assert_called_once_with(character_id)
            mock_repo.update.assert_called_once_with(db_obj=mock_character, obj_in=update_data)

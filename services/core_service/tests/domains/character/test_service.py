import pytest
import uuid
from unittest.mock import AsyncMock, patch

from app.domains.character.service import CharacterService
from app.domains.character.models import Character
from app.domains.character.attribute_models import CharacterAttribute
from app.domains.lorebook.models import Lorebook
from app.domains.chat.models import Chat
from app.domains.persona.models import UserPersona
from app.domains.chat.message_models import Message






@pytest.fixture
def mock_repository():
    return AsyncMock()

@pytest.fixture
def service(mock_repository):
    return CharacterService(mock_repository)

@pytest.mark.asyncio
async def test_delete_character_success_no_creator_id(service, mock_repository):
    character_id = uuid.uuid4()
    mock_character = Character(
        id=character_id,
        creator_id=uuid.uuid4(),
        is_deleted=False,
        is_public=True
    )
    mock_repository.get.return_value = mock_character

    with patch('app.domains.character.service.manager.broadcast', new_callable=AsyncMock) as mock_broadcast:
        result = await service.delete_character(character_id=character_id)

        assert result is True
        mock_repository.get.assert_called_once_with(character_id)
        mock_repository.update.assert_called_once_with(
            db_obj=mock_character,
            obj_in={"is_deleted": True, "is_public": False}
        )
        mock_broadcast.assert_called_once_with({
            "type": "DELETE_CHARACTER",
            "data": {"id": str(character_id)}
        })

@pytest.mark.asyncio
async def test_delete_character_success_with_matching_creator_id(service, mock_repository):
    character_id = uuid.uuid4()
    creator_id = uuid.uuid4()
    mock_character = Character(
        id=character_id,
        creator_id=creator_id,
        is_deleted=False,
        is_public=True
    )
    mock_repository.get.return_value = mock_character

    with patch('app.domains.character.service.manager.broadcast', new_callable=AsyncMock) as mock_broadcast:
        result = await service.delete_character(character_id=character_id, creator_id=creator_id)

        assert result is True
        mock_repository.get.assert_called_once_with(character_id)
        mock_repository.update.assert_called_once_with(
            db_obj=mock_character,
            obj_in={"is_deleted": True, "is_public": False}
        )
        mock_broadcast.assert_called_once_with({
            "type": "DELETE_CHARACTER",
            "data": {"id": str(character_id)}
        })

@pytest.mark.asyncio
async def test_delete_character_not_found(service, mock_repository):
    character_id = uuid.uuid4()
    mock_repository.get.return_value = None

    with patch('app.domains.character.service.manager.broadcast', new_callable=AsyncMock) as mock_broadcast:
        result = await service.delete_character(character_id=character_id)

        assert result is False
        mock_repository.get.assert_called_once_with(character_id)
        mock_repository.update.assert_not_called()
        mock_broadcast.assert_not_called()

@pytest.mark.asyncio
async def test_delete_character_wrong_creator_id(service, mock_repository):
    character_id = uuid.uuid4()
    actual_creator_id = uuid.uuid4()
    wrong_creator_id = uuid.uuid4()

    mock_character = Character(
        id=character_id,
        creator_id=actual_creator_id,
        is_deleted=False,
        is_public=True
    )
    mock_repository.get.return_value = mock_character

    with patch('app.domains.character.service.manager.broadcast', new_callable=AsyncMock) as mock_broadcast:
        result = await service.delete_character(character_id=character_id, creator_id=wrong_creator_id)

        assert result is False
        mock_repository.get.assert_called_once_with(character_id)
        mock_repository.update.assert_not_called()
        mock_broadcast.assert_not_called()

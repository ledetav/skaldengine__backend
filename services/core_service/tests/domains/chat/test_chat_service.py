import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid

from fastapi import BackgroundTasks
from app.domains.chat.service import ChatService
from app.domains.chat.schemas import ChatCreate
from app.domains.character.models import Character
from app.domains.persona.models import UserPersona
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_chat_raises_permission_error_for_different_persona_owner():
    # Arrange
    user_id = uuid.uuid4()
    other_user_id = uuid.uuid4()

    chat_in = ChatCreate(
        character_id=uuid.uuid4(),
        user_persona_id=uuid.uuid4(),
        is_acquainted=False,
        language="ru",
        narrative_voice="third"
    )

    mock_db = MagicMock(spec=AsyncSession)
    mock_db.get = AsyncMock()

    # Setup mock character and persona
    mock_character = Character(id=chat_in.character_id)
    # The persona belongs to `other_user_id`, not the requesting `user_id`
    mock_persona = UserPersona(id=chat_in.user_persona_id, owner_id=other_user_id)

    def side_effect(model, pk):
        if model == Character:
            return mock_character
        elif model == UserPersona:
            return mock_persona
        return None

    mock_db.get.side_effect = side_effect

    mock_background_tasks = MagicMock(spec=BackgroundTasks)

    chat_service = ChatService(repository=MagicMock())

    # Act & Assert
    with pytest.raises(PermissionError) as exc_info:
        await chat_service.create_chat(
            chat_in=chat_in,
            user_id=user_id,
            background_tasks=mock_background_tasks,
            db=mock_db
        )

    assert str(exc_info.value) == "You can only use your own personas"

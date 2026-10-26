import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.core.prompt_pipeline.context import PipelineContext
from app.core.prompt_pipeline.stages.lorebook_stage import get_stems, LorebookStage
from app.core.prompt_pipeline.stages.scenario_stage import ScenarioStage
from app.core.prompt_pipeline.stages.history_stage import HistoryStage
from app.core.prompt_pipeline.stages.assembler_stage import AssemblerStage
from app.domains.chat.models import Chat, ChatCheckpoint
from app.domains.character.models import Character
from app.domains.persona.models import UserPersona
from app.domains.scenario.models import Scenario
from app.domains.lorebook.models import Lorebook, LorebookEntry


def test_get_stems_handles_russian_and_english():
    text = "Драконы летали над Castle of Shadows"
    stems = get_stems(text)
    # Stems for Russian and English words >= 3 chars
    assert "драко" in stems
    assert "летал" in stems
    assert "castl" in stems
    assert "shado" in stems


@pytest.mark.asyncio
async def test_scenario_stage_detects_stall_intervention():
    db = MagicMock()
    chat_id = uuid4()
    user = MagicMock()

    context = PipelineContext(db=db, chat_id=chat_id, current_user=user)
    context.chat = MagicMock(spec=Chat)
    context.chat.mode = "scenario"

    # Mock checkpoint with messages_spent >= 8
    checkpoint = MagicMock(spec=ChatCheckpoint)
    checkpoint.goal_description = "Find the ancient key"
    checkpoint.messages_spent = 9

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = checkpoint
    db.execute = AsyncMock(return_value=result_mock)

    stage = ScenarioStage()
    await stage.process(context)

    assert "[CRITICAL NARRATIVE INTERVENTION]" in context.scenario_directive
    assert "Find the ancient key" in context.scenario_directive


@pytest.mark.asyncio
async def test_scenario_stage_normal_goal_guidance():
    db = MagicMock()
    chat_id = uuid4()
    user = MagicMock()

    context = PipelineContext(db=db, chat_id=chat_id, current_user=user)
    context.chat = MagicMock(spec=Chat)
    context.chat.mode = "scenario"

    checkpoint = MagicMock(spec=ChatCheckpoint)
    checkpoint.goal_description = "Enter the throne room"
    checkpoint.messages_spent = 3

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = checkpoint
    db.execute = AsyncMock(return_value=result_mock)

    stage = ScenarioStage()
    await stage.process(context)

    assert "CURRENT SCENARIO GOAL: Enter the throne room" in context.scenario_directive


@pytest.mark.asyncio
async def test_assembler_stage_formats_russian_reality_check():
    db = MagicMock()
    chat_id = uuid4()
    user = MagicMock()
    user.birth_date = None

    context = PipelineContext(db=db, chat_id=chat_id, current_user=user)
    context.chat = MagicMock(spec=Chat)
    context.chat.mode = "sandbox"
    context.chat.language = "Russian"
    context.chat.narrative_voice = "Second Person"
    context.chat.is_acquainted = True
    context.chat.relationship_dynamic = "Друзья детства"
    context.chat.custom_plot_hook = "Встреча в таверне"
    context.chat.custom_location = "Таверна Гарцующий пони"

    context.character = MagicMock(spec=Character)
    context.character.name = "Аэлита"
    context.character.gender = "Женский"
    context.character.age = "24"
    context.character.appearance = "Рыжие волосы, зеленые глаза"
    context.character.personality = "Смелая, решительная"
    context.character.nsfw_allowed = False

    context.persona = MagicMock(spec=UserPersona)
    context.persona.name = "Александр"
    context.persona.gender = "Мужской"
    context.persona.age = "28"
    context.persona.appearance = "Высокий брюнет"
    context.persona.personality = "Спокойный"

    context.core_attributes = ["Мастер клинка"]
    context.persona_core_attributes = ["Странник"]
    context.memories = ["Победили разбойников на тракте"]

    stage = AssemblerStage()
    payload = await stage.process(context, user_text="Привет, Аэлита!")

    assert "model" in payload
    assert payload["stream"] is True
    system_content = payload["messages"][0]["content"]

    # Verify Russian reality check is present
    assert "[Проверка реальности: Я сохраняю свою суть, я не льщу, мой темп соразмерен. Ответ готов.]" in system_content
    # Verify SFW constraint is injected
    assert "[CHARACTER CONSTRAINT]: This character is strictly SFW" in system_content
    # Verify profiles and memory
    assert "Аэлита" in system_content
    assert "Александр" in system_content
    assert "Победили разбойников на тракте" in system_content
    assert payload["messages"][-1] == {"role": "user", "content": "Привет, Аэлита!"}

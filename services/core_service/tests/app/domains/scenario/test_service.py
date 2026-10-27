"""
Модульные тесты для сервиса сценариев (ScenarioService).
"""

import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.domains.scenario.service import ScenarioService
from app.domains.scenario.schemas import ScenarioCreate, ScenarioUpdate
from app.domains.scenario.models import Scenario


@pytest.fixture
def mock_repository():
    """Фикстура мока репозитория сценариев."""
    return AsyncMock()


@pytest.fixture
def scenario_service(mock_repository):
    """Фикстура экземпляра ScenarioService с мок-репозиторием."""
    return ScenarioService(repository=mock_repository)


@pytest.mark.asyncio
async def test_get_scenarios(scenario_service, mock_repository):
    """Тест получения списка сценариев с пагинацией."""
    mock_scenarios = [Scenario(id=uuid4(), title="Test", description="D", start_point="S", end_point="E")]
    mock_repository.get_multi_with_counts.return_value = mock_scenarios

    result = await scenario_service.get_scenarios(skip=10, limit=5)

    mock_repository.get_multi_with_counts.assert_called_once_with(skip=10, limit=5)
    assert result == mock_scenarios


@pytest.mark.asyncio
async def test_get_by_character(scenario_service, mock_repository):
    """Проверка получения списка сценариев, привязанных к конкретному персонажу."""
    char_id = uuid4()
    mock_scenarios = [Scenario(id=uuid4(), title="Test", character_id=char_id, description="D", start_point="S", end_point="E")]
    mock_repository.get_by_character.return_value = mock_scenarios

    result = await scenario_service.get_by_character(char_id)

    mock_repository.get_by_character.assert_called_once_with(char_id)
    assert result == mock_scenarios

@pytest.mark.asyncio
@patch("app.core.broadcast.manager.broadcast")
async def test_create_scenario(mock_broadcast, scenario_service, mock_repository):
    """Проверка создания общего сценария и рассылки WebSocket-события NEW_SCENARIO."""
    scenario_in = ScenarioCreate(
        title="New Scenario",
        location="Castle",
        description="Desc",
        start_point="A",
        end_point="B",
        internal_description="Internal"
    )
    mock_scenario = Scenario(id=uuid4(), **scenario_in.model_dump())
    mock_repository.create.return_value = mock_scenario

    result = await scenario_service.create_scenario(scenario_in)

    mock_repository.create.assert_called_once_with(obj_in=scenario_in)
    assert result == mock_scenario
    assert result.chats_count == 0
    mock_broadcast.assert_called_once_with({
        "type": "NEW_SCENARIO",
        "data": {
            "id": str(mock_scenario.id),
            "title": "New Scenario",
            "location": "Castle",
            "description": "Desc",
            "start_point": "A",
            "end_point": "B",
            "internal_description": "Internal",
            "character_id": None,
            "chats_count": 0
        }
    })

@pytest.mark.asyncio
@patch("app.core.broadcast.manager.broadcast")
async def test_create_scenario_with_character(mock_broadcast, scenario_service, mock_repository):
    """Проверка создания сценария с явной привязкой к ID персонажа."""
    char_id = uuid4()
    scenario_in = ScenarioCreate(
        title="Char Scenario",
        character_id=char_id,
        description="Desc",
        start_point="A",
        end_point="B"
    )
    mock_scenario = Scenario(id=uuid4(), **scenario_in.model_dump())
    mock_repository.create.return_value = mock_scenario

    result = await scenario_service.create_scenario(scenario_in)

    mock_broadcast.assert_called_once_with({
        "type": "NEW_SCENARIO",
        "data": {
            "id": str(mock_scenario.id),
            "title": "Char Scenario",
            "location": None,
            "description": "Desc",
            "start_point": "A",
            "end_point": "B",
            "internal_description": None,
            "character_id": str(char_id),
            "chats_count": 0
        }
    })

@pytest.mark.asyncio
@patch("app.core.broadcast.manager.broadcast")
async def test_update_scenario_success(mock_broadcast, scenario_service, mock_repository):
    """Проверка успешного обновления сценария и рассылки события UPDATE_SCENARIO."""
    scenario_id = uuid4()
    existing_scenario = Scenario(id=scenario_id, title="Old", description="D", start_point="S", end_point="E")
    update_data = ScenarioUpdate(title="New")
    updated_scenario = Scenario(id=scenario_id, title="New", description="D", start_point="S", end_point="E")
    updated_scenario.chats_count = 5

    mock_repository.get.return_value = existing_scenario
    mock_repository.update.return_value = updated_scenario
    mock_repository.get_with_count.return_value = updated_scenario

    result = await scenario_service.update_scenario(scenario_id, update_data)

    mock_repository.get.assert_called_once_with(scenario_id)
    mock_repository.update.assert_called_once_with(db_obj=existing_scenario, obj_in=update_data)
    mock_repository.get_with_count.assert_called_once_with(scenario_id)
    assert result == updated_scenario
    mock_broadcast.assert_called_once_with({
        "type": "UPDATE_SCENARIO",
        "data": {
            "id": str(scenario_id),
            "title": "New",
            "location": None,
            "description": "D",
            "start_point": "S",
            "end_point": "E",
            "internal_description": None,
            "character_id": None,
            "chats_count": 5
        }
    })

@pytest.mark.asyncio
async def test_update_scenario_not_found(scenario_service, mock_repository):
    """Проверка возврата None при попытке обновления несуществующего сценария."""
    scenario_id = uuid4()
    update_data = ScenarioUpdate(title="New")

    mock_repository.get.return_value = None

    result = await scenario_service.update_scenario(scenario_id, update_data)

    mock_repository.get.assert_called_once_with(scenario_id)
    mock_repository.update.assert_not_called()
    assert result is None

@pytest.mark.asyncio
@patch("app.core.broadcast.manager.broadcast")
async def test_delete_scenario_success(mock_broadcast, scenario_service, mock_repository):
    """Проверка успешного удаления сценария и рассылки события DELETE_SCENARIO."""
    scenario_id = uuid4()
    existing_scenario = Scenario(id=scenario_id, title="Old", description="D", start_point="S", end_point="E")

    mock_repository.get.return_value = existing_scenario
    mock_repository.delete.return_value = True

    result = await scenario_service.delete_scenario(scenario_id)

    mock_repository.get.assert_called_once_with(scenario_id)
    mock_repository.delete.assert_called_once_with(id=scenario_id)
    assert result is True
    mock_broadcast.assert_called_once_with({
        "type": "DELETE_SCENARIO",
        "data": {"id": str(scenario_id)}
    })

@pytest.mark.asyncio
async def test_delete_scenario_not_found(scenario_service, mock_repository):
    """Проверка возврата False при попытке удаления несуществующего сценария."""
    scenario_id = uuid4()

    mock_repository.get.return_value = None

    result = await scenario_service.delete_scenario(scenario_id)

    mock_repository.get.assert_called_once_with(scenario_id)
    mock_repository.delete.assert_not_called()
    assert result is False

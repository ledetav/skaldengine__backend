import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from app.domains.scenario.service import ScenarioService
from app.domains.scenario.schemas import ScenarioCreate, ScenarioUpdate
from app.domains.scenario.models import Scenario

@pytest.fixture
def mock_repository():
    return AsyncMock()

@pytest.fixture
def scenario_service(mock_repository):
    return ScenarioService(repository=mock_repository)

@pytest.mark.asyncio
async def test_get_scenarios(scenario_service, mock_repository):
    mock_scenarios = [Scenario(id=uuid4(), title="Test", description="D", start_point="S", end_point="E")]
    mock_repository.get_multi.return_value = mock_scenarios

    result = await scenario_service.get_scenarios(skip=10, limit=5)

    mock_repository.get_multi.assert_called_once_with(skip=10, limit=5)
    assert result == mock_scenarios

@pytest.mark.asyncio
async def test_get_by_character(scenario_service, mock_repository):
    char_id = uuid4()
    mock_scenarios = [Scenario(id=uuid4(), title="Test", character_id=char_id, description="D", start_point="S", end_point="E")]
    mock_repository.get_by_character.return_value = mock_scenarios

    result = await scenario_service.get_by_character(char_id)

    mock_repository.get_by_character.assert_called_once_with(char_id)
    assert result == mock_scenarios

@pytest.mark.asyncio
async def test_create_scenario(scenario_service, mock_repository):
    scenario_in = ScenarioCreate(
        title="New Scenario",
        description="Desc",
        start_point="A",
        end_point="B"
    )
    mock_scenario = Scenario(id=uuid4(), **scenario_in.model_dump())
    mock_repository.create.return_value = mock_scenario

    result = await scenario_service.create_scenario(scenario_in)

    mock_repository.create.assert_called_once_with(obj_in=scenario_in)
    assert result == mock_scenario

@pytest.mark.asyncio
async def test_update_scenario_success(scenario_service, mock_repository):
    scenario_id = uuid4()
    existing_scenario = Scenario(id=scenario_id, title="Old", description="D", start_point="S", end_point="E")
    update_data = ScenarioUpdate(title="New")
    updated_scenario = Scenario(id=scenario_id, title="New", description="D", start_point="S", end_point="E")

    mock_repository.get.return_value = existing_scenario
    mock_repository.update.return_value = updated_scenario

    result = await scenario_service.update_scenario(scenario_id, update_data)

    mock_repository.get.assert_called_once_with(scenario_id)
    mock_repository.update.assert_called_once_with(db_obj=existing_scenario, obj_in=update_data)
    assert result == updated_scenario

@pytest.mark.asyncio
async def test_update_scenario_not_found(scenario_service, mock_repository):
    scenario_id = uuid4()
    update_data = ScenarioUpdate(title="New")

    mock_repository.get.return_value = None

    result = await scenario_service.update_scenario(scenario_id, update_data)

    mock_repository.get.assert_called_once_with(scenario_id)
    mock_repository.update.assert_not_called()
    assert result is None

@pytest.mark.asyncio
async def test_delete_scenario_success(scenario_service, mock_repository):
    scenario_id = uuid4()
    existing_scenario = Scenario(id=scenario_id, title="Old", description="D", start_point="S", end_point="E")

    mock_repository.get.return_value = existing_scenario
    mock_repository.delete.return_value = True

    result = await scenario_service.delete_scenario(scenario_id)

    mock_repository.get.assert_called_once_with(scenario_id)
    mock_repository.delete.assert_called_once_with(id=scenario_id)
    assert result is True

@pytest.mark.asyncio
async def test_delete_scenario_not_found(scenario_service, mock_repository):
    scenario_id = uuid4()

    mock_repository.get.return_value = None

    result = await scenario_service.delete_scenario(scenario_id)

    mock_repository.get.assert_called_once_with(scenario_id)
    mock_repository.delete.assert_not_called()
    assert result is False

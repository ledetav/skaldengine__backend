import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.domains.user.auth_service import AuthService
from app.domains.user.models import User

@pytest.fixture
def auth_service():
    repository_mock = AsyncMock()
    return AuthService(repository=repository_mock)

@pytest.mark.asyncio
async def test_authenticate_user_not_found(auth_service):
    # Setup
    auth_service.repository.get_by_email_or_login.return_value = None

    # Execute
    result = await auth_service.authenticate("invalid_user", "password123")

    # Assert
    assert result is None
    auth_service.repository.get_by_email_or_login.assert_called_once_with("invalid_user")

@pytest.mark.asyncio
@patch('app.domains.user.auth_service.verify_password')
async def test_authenticate_invalid_password(mock_verify_password, auth_service):
    # Setup
    mock_user = MagicMock(spec=User)
    mock_user.password_hash = "hashed_password"
    auth_service.repository.get_by_email_or_login.return_value = mock_user

    mock_verify_password.return_value = False

    # Execute
    result = await auth_service.authenticate("valid_user", "wrong_password")

    # Assert
    assert result is None
    auth_service.repository.get_by_email_or_login.assert_called_once_with("valid_user")
    mock_verify_password.assert_called_once_with("wrong_password", "hashed_password")

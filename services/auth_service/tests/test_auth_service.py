import os
import sys
from unittest.mock import MagicMock, AsyncMock

# 1. Mock external libraries before they are imported by app components
for module_name in [
    "sqlalchemy", "sqlalchemy.orm", "sqlalchemy.sql", "sqlalchemy.ext.asyncio",
    "sqlalchemy.schema", "sqlalchemy.types", "jose", "bcrypt", "passlib", "passlib.context",
    "pydantic", "pydantic_settings",
]:
    sys.modules[module_name] = MagicMock()

# Setup paths to find 'app' and 'shared'
current_dir = os.path.dirname(os.path.abspath(__file__))
service_dir = os.path.abspath(os.path.join(current_dir, ".."))
root_dir = os.path.abspath(os.path.join(service_dir, "..", ".."))

if service_dir not in sys.path:
    sys.path.insert(0, service_dir)
if root_dir not in sys.path:
    sys.path.insert(1, root_dir)

# Mock 'shared' module components that use Generic/subscripting
class DummyGenericMeta(type):
    def __getitem__(cls, item):
        return cls

class DummyGeneric(metaclass=DummyGenericMeta):
    def __init__(self, repository=None):
        self.repository = repository

sys.modules["shared"] = MagicMock()
sys.modules["shared.base"] = MagicMock()
sys.modules["shared.base.service"] = MagicMock(BaseService=DummyGeneric)
sys.modules["shared.base.repository"] = MagicMock(BaseRepository=DummyGeneric)

# Mock app.core.config before it's imported
mock_settings = MagicMock()
mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 60
sys.modules["app.core.config"] = MagicMock(settings=mock_settings)

# Mock app.db.base
class DummyBase:
    pass
sys.modules["app.db.base"] = MagicMock(Base=DummyBase)

# 2. Setup specific mocks for security functions
from unittest.mock import patch
import app.core.security as mock_security
mock_security.verify_password = MagicMock()
mock_security.create_access_token = MagicMock()

# 3. Import the class under test
from app.domains.user.auth_service import AuthService
from app.core.security import TokenPayload
from app.domains.user.models import User

from unittest import IsolatedAsyncioTestCase

class TestAuthService(IsolatedAsyncioTestCase):
    def setUp(self):
        self.repository = AsyncMock()
        self.service = AuthService(repository=self.repository)

    @patch('app.domains.user.auth_service.verify_password')
    @patch('app.domains.user.auth_service.create_access_token')
    async def test_authenticate_success(self, mock_create_access_token, mock_verify_password):
        # Arrange
        identifier = "test@example.com"
        password = "password123"

        user = MagicMock(spec=User)
        user.id = "user-id"
        user.password_hash = "$2b$12$Lb1L9UREHfkdzuQ07DFzQO7NsFeAa0dF8GWVZsZXODyP0yZsOYK1C"
        user.role = "user"
        user.login = "testuser"
        user.username = "testusername"
        user.full_name = "Test User"
        user.birth_date = "2000-01-01"
        user.polza_api_key = "api-key"

        self.repository.get_by_email_or_login.return_value = user
        mock_verify_password.return_value = True
        mock_create_access_token.return_value = "fake-jwt-token"

        # Act
        result = await self.service.authenticate(identifier, password)

        # Assert
        self.repository.get_by_email_or_login.assert_called_once_with(identifier)
        mock_security.verify_password.assert_called_once_with(password, "hashed_password")
        mock_security.create_access_token.assert_called_once()

        call_args = mock_security.create_access_token.call_args[1]
        self.assertIn('payload', call_args)
        self.assertIn('expires_delta', call_args)
        self.assertIsInstance(call_args['payload'], TokenPayload)
        self.assertEqual(call_args['payload'].subject, 'user-id')
        self.assertEqual(result, {
            "access_token": "fake-jwt-token",
            "token_type": "bearer",
        })

    async def test_authenticate_user_not_found(self):
        # Arrange
        self.repository.get_by_email_or_login.return_value = None

        # Act
        result = await self.service.authenticate("unknown@example.com", "password")

        # Assert
        self.assertIsNone(result)

    @patch('app.domains.user.auth_service.verify_password')
    async def test_authenticate_wrong_password(self, mock_verify_password):
        # Arrange
        user = MagicMock(spec=User)
        user.password_hash = "$2b$12$Lb1L9UREHfkdzuQ07DFzQO7NsFeAa0dF8GWVZsZXODyP0yZsOYK1C"
        self.repository.get_by_email_or_login.return_value = user
        mock_verify_password.return_value = False

        # Act
        result = await self.service.authenticate("test@example.com", "wrong_password")

        # Assert
        self.assertIsNone(result)

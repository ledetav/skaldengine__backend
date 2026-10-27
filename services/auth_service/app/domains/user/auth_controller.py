"""Контроллер обработки запросов входа и регистрации."""

from fastapi import status
from fastapi.security import OAuth2PasswordRequestForm
from shared.base.controller import BaseController
from .auth_service import AuthService
from .schemas import Token, UserCreate, UserResponse
from shared.schemas.response import BaseResponse


class AuthController(BaseController):
    """Контроллер процедур аутентификации и регистрации."""

    def __init__(self, auth_service: AuthService):
        """Инициализация контроллера аутентификации.

        Args:
            auth_service: Сервис аутентификации.
        """
        self.auth_service = auth_service

    async def login(self, form_data: OAuth2PasswordRequestForm) -> BaseResponse:
        """Выполняет вход пользователя по логину/email и паролю."""
        result = await self.auth_service.authenticate(form_data.username, form_data.password)
        if not result:
            self.handle_error("Неверный логин или пароль", status_code=status.HTTP_400_BAD_REQUEST)
        return self.handle_success(data=result)

    async def register(self, user_in: UserCreate) -> BaseResponse:
        """Регистрирует нового пользователя."""
        try:
            user = await self.auth_service.register(user_in)
            return self.handle_success(data=UserResponse.model_validate(user))
        except ValueError as e:
            self.handle_error(str(e), status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            self.handle_error(str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


from fastapi import status
from fastapi.security import OAuth2PasswordRequestForm
from shared.base.controller import BaseController
from .auth_service import AuthService
from .schemas import Token, UserCreate, UserResponse
from shared.schemas.response import BaseResponse

class AuthController(BaseController):
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    async def login(self, form_data: OAuth2PasswordRequestForm) -> BaseResponse:
        result = await self.auth_service.authenticate(form_data.username, form_data.password)
        if not result:
            self.handle_error("Incorrect email or password", status_code=status.HTTP_400_BAD_REQUEST)
        return self.handle_success(data=result)

    async def register(self, user_in: UserCreate) -> BaseResponse:
        try:
            user = await self.auth_service.register(user_in)
            return self.handle_success(data=user)
        except ValueError as e:
            self.handle_error(str(e), status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            self.handle_error("Internal server error", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

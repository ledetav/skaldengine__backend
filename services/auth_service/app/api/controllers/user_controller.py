from fastapi import status
from app.api.base_controller import BaseController
from app.services.user_service import UserService
from app.models.user import User
from app.schemas.user import LoginUpdate, UsernameUpdate, EmailUpdate, PasswordUpdate, FullNameUpdate, ProfileUpdate
from app.schemas.response import BaseResponse

class UserController(BaseController):
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def update_login(self, user: User, update_in: LoginUpdate) -> BaseResponse:
        try:
            updated_user = await self.user_service.update_login(user, update_in)
            return self.handle_success(data=updated_user)
        except ValueError as e:
            self.handle_error(str(e))

    async def update_username(self, user: User, update_in: UsernameUpdate) -> BaseResponse:
        try:
            updated_user = await self.user_service.update_username(user, update_in)
            return self.handle_success(data=updated_user)
        except ValueError as e:
            self.handle_error(str(e))

    async def update_email(self, user: User, update_in: EmailUpdate) -> BaseResponse:
        try:
            updated_user = await self.user_service.update_email(user, update_in)
            return self.handle_success(data=updated_user)
        except ValueError as e:
            self.handle_error(str(e))

    async def update_full_name(self, user: User, update_in: FullNameUpdate) -> BaseResponse:
        updated_user = await self.user_service.update_full_name(user, update_in)
        return self.handle_success(data=updated_user)

    async def update_password(self, user: User, update_in: PasswordUpdate) -> BaseResponse:
        try:
            await self.user_service.update_password(user, update_in)
            return self.handle_success(data={"message": "Password updated successfully"})
        except ValueError as e:
            self.handle_error(str(e))

    async def update_profile(self, user: User, update_in: ProfileUpdate) -> BaseResponse:
        updated_user = await self.user_service.update_profile(user, update_in)
        return self.handle_success(data=updated_user)

    async def delete_user(self, user: User) -> BaseResponse:
        await self.user_service.delete_user(user.id)
        return self.handle_success(data=None)

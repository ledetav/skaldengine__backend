from fastapi import status
from shared.base.controller import BaseController
from .service import UserService
from app.domains.user.models import User
from .schemas import UserUpdate, ProfileUpdate, LoginUpdate, UsernameUpdate, EmailUpdate, PasswordUpdate, FullNameUpdate
from shared.schemas.response import BaseResponse

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

    async def update_me(self, user: User, update_in: UserUpdate) -> BaseResponse:
        try:
            updated_user = await self.user_service.update_me(user, update_in)
            return self.handle_success(data=updated_user)
        except ValueError as e:
            self.handle_error(str(e))

    async def delete_user(self, user: User) -> BaseResponse:
        await self.user_service.delete_user(user.id)
        return self.handle_success(data=None)

    async def get_public_profile(self, username: str) -> BaseResponse:
        user = await self.user_service.get_by_username(username)
        if not user:
            self.handle_error("User not found", status_code=status.HTTP_404_NOT_FOUND)
        
        from .schemas import PublicProfileResponse
        
        public_data = PublicProfileResponse.model_validate(user)
        return self.handle_success(data=public_data)

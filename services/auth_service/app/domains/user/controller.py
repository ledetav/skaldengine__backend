"""Контроллер обработки запросов управления пользователями."""

from typing import List
from uuid import UUID
from fastapi import status
from shared.base.controller import BaseController
from .service import UserService
from app.domains.user.models import User
from .schemas import UserUpdate, ProfileUpdate, LoginUpdate, UsernameUpdate, EmailUpdate, PasswordUpdate, FullNameUpdate, UserResponse, RoleUpdate
from shared.schemas.response import BaseResponse


class UserController(BaseController):
    """Контроллер пользовательских операций и административных действий."""

    def __init__(self, user_service: UserService):
        """Инициализация контроллера пользователей.

        Args:
            user_service: Сервис бизнес-логики пользователей.
        """
        self.user_service = user_service

    async def update_login(self, user: User, update_in: LoginUpdate) -> BaseResponse:
        """Обновляет логин текущего пользователя."""
        try:
            updated_user = await self.user_service.update_login(user, update_in)
            return self.handle_success(data=UserResponse.model_validate(updated_user))
        except ValueError as e:
            self.handle_error(str(e))

    async def update_username(self, user: User, update_in: UsernameUpdate) -> BaseResponse:
        """Обновляет публичный никнейм (@handle) текущего пользователя."""
        try:
            updated_user = await self.user_service.update_username(user, update_in)
            return self.handle_success(data=UserResponse.model_validate(updated_user))
        except ValueError as e:
            self.handle_error(str(e))

    async def update_email(self, user: User, update_in: EmailUpdate) -> BaseResponse:
        """Обновляет email текущего пользователя."""
        try:
            updated_user = await self.user_service.update_email(user, update_in)
            return self.handle_success(data=UserResponse.model_validate(updated_user))
        except ValueError as e:
            self.handle_error(str(e))

    async def update_full_name(self, user: User, update_in: FullNameUpdate) -> BaseResponse:
        """Обновляет полное имя текущего пользователя."""
        updated_user = await self.user_service.update_full_name(user, update_in)
        return self.handle_success(data=UserResponse.model_validate(updated_user))

    async def update_password(self, user: User, update_in: PasswordUpdate) -> BaseResponse:
        """Обновляет пароль текущего пользователя."""
        try:
            await self.user_service.update_password(user, update_in)
            return self.handle_success(data={"message": "Пароль успешно обновлен"})
        except ValueError as e:
            self.handle_error(str(e))

    async def update_profile(self, user: User, update_in: ProfileUpdate) -> BaseResponse:
        """Обновляет данные профиля (аватар, обложку, информацию о себе)."""
        updated_user = await self.user_service.update_profile(user, update_in)
        return self.handle_success(data=UserResponse.model_validate(updated_user))

    async def update_me(self, user: User, update_in: UserUpdate) -> BaseResponse:
        """Комплексно обновляет профиль текущего пользователя."""
        try:
            updated_user = await self.user_service.update_me(user, update_in)
            return self.handle_success(data=UserResponse.model_validate(updated_user))
        except ValueError as e:
            self.handle_error(str(e))

    async def delete_user(self, user: User) -> BaseResponse:
        """Удаляет профиль текущего пользователя."""
        await self.user_service.delete_user(user.id)
        return self.handle_success(data=None)

    async def admin_delete_user(self, current_user: User, user_id: str) -> BaseResponse:
        """Удаляет пользователя от лица администратора."""
        if current_user.role != "admin":
            self.handle_error("Только администраторы могут удалять пользователей", status_code=status.HTTP_403_FORBIDDEN)
        user_to_delete = await self.user_service.get(id=user_id)
        if not user_to_delete:
            self.handle_error("Пользователь не найден", status_code=status.HTTP_404_NOT_FOUND)
        if str(current_user.id) == str(user_id):
            self.handle_error("Нельзя удалить собственную учетную запись", status_code=status.HTTP_400_BAD_REQUEST)
        await self.user_service.delete_user(user_id)
        return self.handle_success(data=None)

    async def admin_update_role(self, current_user: User, user_id: str, new_role: str) -> BaseResponse:
        """Изменяет роль пользователя от лица администратора."""
        if current_user.role != "admin":
            self.handle_error("Только администраторы могут изменять роли", status_code=status.HTTP_403_FORBIDDEN)
        user_to_update = await self.user_service.get(id=user_id)
        if not user_to_update:
            self.handle_error("Пользователь не найден", status_code=status.HTTP_404_NOT_FOUND)
        if str(current_user.id) == str(user_id):
            self.handle_error("Нельзя изменить роль собственной учетной записи", status_code=status.HTTP_400_BAD_REQUEST)
        updated_user = await self.user_service.update_role(user_to_update, new_role)
        return self.handle_success(data=UserResponse.model_validate(updated_user))

    async def get_public_profile(self, username: str) -> BaseResponse:
        """Возвращает публичный профиль пользователя по юзернейму."""
        user = await self.user_service.get_by_username(username)
        if not user:
            self.handle_error("Пользователь не найден", status_code=status.HTTP_404_NOT_FOUND)
        
        from .schemas import PublicProfileResponse
        
        public_data = PublicProfileResponse.model_validate(user)
        return self.handle_success(data=public_data)

    async def get_all_users(self, skip: int = 0, limit: int = 20) -> BaseResponse:
        """Возвращает список всех пользователей с пагинацией."""
        users, total = await self.user_service.get_all_users(skip=skip, limit=limit)
        return self.handle_success(data={"items": [UserResponse.model_validate(u) for u in users], "total": total})

    async def get_users_by_ids(self, user_ids: List[UUID]) -> BaseResponse:
        """Возвращает публичные профили пользователей по списку ID."""
        from .schemas import PublicProfileResponse
        users = await self.user_service.get_by_ids(user_ids)
        return self.handle_success(data=[PublicProfileResponse.model_validate(u) for u in users])


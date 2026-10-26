"""Сервис управления пользователями и их профилями."""

from typing import Optional, Any
from shared.base.service import BaseService
from .repository import UserRepository
from .models import User
from app.core import security
from .schemas import UserUpdate, LoginUpdate, UsernameUpdate, EmailUpdate, PasswordUpdate, FullNameUpdate, ProfileUpdate, RoleUpdate


class UserService(BaseService[UserRepository]):
    """Сервис бизнес-логики управления учетными записями и профилями пользователей."""

    async def update_login(self, user: User, update_in: LoginUpdate) -> User:
        """Обновляет логин пользователя.

        Raises:
            ValueError: Если новый логин уже занят другим пользователем.
        """
        existing = await self.repository.get_by_email_or_login(update_in.new_login)
        if existing:
            raise ValueError("Логин уже занят")
        return await self.repository.update(db_obj=user, obj_in={"login": update_in.new_login})

    async def update_username(self, user: User, update_in: UsernameUpdate) -> User:
        """Обновляет публичный никнейм (@handle) пользователя.

        Raises:
            ValueError: Если имя пользователя уже занято.
        """
        query_result = await self.repository.check_existence(email="", login="", username=update_in.new_username)
        if query_result:
            raise ValueError("Имя пользователя уже занято")
        return await self.repository.update(db_obj=user, obj_in={"username": update_in.new_username})

    async def update_email(self, user: User, update_in: EmailUpdate) -> User:
        """Обновляет email адрес пользователя.

        Raises:
            ValueError: Если email уже зарегистрирован.
        """
        query_result = await self.repository.check_existence(email=update_in.new_email, login="", username="")
        if query_result:
            raise ValueError("Email уже зарегистрирован")
        return await self.repository.update(db_obj=user, obj_in={"email": update_in.new_email})

    async def update_full_name(self, user: User, update_in: FullNameUpdate) -> User:
        """Обновляет полное имя пользователя."""
        return await self.repository.update(db_obj=user, obj_in={"full_name": update_in.full_name})

    async def update_password(self, user: User, update_in: PasswordUpdate) -> None:
        """Обновляет пароль пользователя с предварительным хешированием."""
        await self.repository.update(
            db_obj=user, 
            obj_in={"password_hash": security.get_password_hash(update_in.new_password)}
        )

    async def update_profile(self, user: User, update_in: ProfileUpdate) -> User:
        """Обновляет данные профиля (аватар, обложку, описание о себе)."""
        update_data = update_in.model_dump(exclude_unset=True)
        return await self.repository.update(db_obj=user, obj_in=update_data)

    async def update_me(self, user: User, update_in: UserUpdate) -> User:
        """Комплексно обновляет данные текущего пользователя.

        Raises:
            ValueError: Если логин, username или email уже заняты.
        """
        update_data = update_in.model_dump(exclude_unset=True)
        if "login" in update_data:
            existing = await self.repository.get_by_email_or_login(update_data["login"])
            if existing and existing.id != user.id:
                raise ValueError("Логин уже занят")
        if "username" in update_data:
            query_result = await self.repository.check_existence(email="", login="", username=update_data["username"])
            if query_result and query_result.id != user.id:
                raise ValueError("Имя пользователя уже занято")
        if "email" in update_data:
            query_result = await self.repository.check_existence(email=update_data["email"], login="", username="")
            if query_result and query_result.id != user.id:
                raise ValueError("Email уже зарегистрирован")
        return await self.repository.update(db_obj=user, obj_in=update_data)

    async def delete_user(self, user_id: Any) -> None:
        """Удаляет пользователя по его идентификатору."""
        await self.repository.delete(id=user_id)

    async def get_by_username(self, username: str) -> Optional[User]:
        """Возвращает пользователя по публичному никнейму."""
        return await self.repository.get_by_username(username)

    async def get_by_ids(self, ids: list[Any]) -> list[User]:
        """Возвращает список пользователей по списку идентификаторов."""
        return await self.repository.get_multi_by_ids(ids)

    async def get(self, id: Any) -> Optional[User]:
        """Возвращает пользователя по первичному ключу ID."""
        return await self.repository.get(id)

    async def update_role(self, user: User, role: str) -> User:
        """Обновляет роль пользователя в системе."""
        return await self.repository.update(db_obj=user, obj_in={"role": role})

    async def get_all_users(self, skip: int = 0, limit: int = 20) -> tuple[list, int]:
        """Возвращает список пользователей с пагинацией и их общее количество."""
        return await self.repository.get_multi_with_count(skip=skip, limit=limit)


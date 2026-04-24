from typing import Optional, Any
from shared.base.service import BaseService
from .repository import UserRepository
from .models import User
from app.core import security
from .schemas import UserUpdate, LoginUpdate, UsernameUpdate, EmailUpdate, PasswordUpdate, FullNameUpdate, ProfileUpdate, RoleUpdate

class UserService(BaseService[UserRepository]):
    async def update_login(self, user: User, update_in: LoginUpdate) -> User:
        existing = await self.repository.get_by_email_or_login(update_in.new_login)
        if existing:
            raise ValueError("Login already taken")
        return await self.repository.update(db_obj=user, obj_in={"login": update_in.new_login})

    async def update_username(self, user: User, update_in: UsernameUpdate) -> User:
        query_result = await self.repository.check_existence(email="", login="", username=update_in.new_username)
        if query_result:
            raise ValueError("Username already taken")
        return await self.repository.update(db_obj=user, obj_in={"username": update_in.new_username})

    async def update_email(self, user: User, update_in: EmailUpdate) -> User:
        query_result = await self.repository.check_existence(email=update_in.new_email, login="", username="")
        if query_result:
            raise ValueError("Email already registered")
        return await self.repository.update(db_obj=user, obj_in={"email": update_in.new_email})

    async def update_full_name(self, user: User, update_in: FullNameUpdate) -> User:
        return await self.repository.update(db_obj=user, obj_in={"full_name": update_in.full_name})

    async def update_password(self, user: User, update_in: PasswordUpdate) -> None:
        await self.repository.update(
            db_obj=user, 
            obj_in={"password_hash": security.get_password_hash(update_in.new_password)}
        )

    async def update_profile(self, user: User, update_in: ProfileUpdate) -> User:
        update_data = update_in.model_dump(exclude_unset=True)
        return await self.repository.update(db_obj=user, obj_in=update_data)

    async def update_me(self, user: User, update_in: UserUpdate) -> User:
        update_data = update_in.model_dump(exclude_unset=True)
        if "login" in update_data:
            existing = await self.repository.get_by_email_or_login(update_data["login"])
            if existing and existing.id != user.id:
                raise ValueError("Login already taken")
        if "username" in update_data:
            query_result = await self.repository.check_existence(email="", login="", username=update_data["username"])
            if query_result and query_result.id != user.id:
                raise ValueError("Username already taken")
        if "email" in update_data:
            query_result = await self.repository.check_existence(email=update_data["email"], login="", username="")
            if query_result and query_result.id != user.id:
                raise ValueError("Email already registered")
        return await self.repository.update(db_obj=user, obj_in=update_data)

    async def delete_user(self, user_id: Any) -> None:
        await self.repository.delete(id=user_id)

    async def get_by_username(self, username: str) -> Optional[User]:
        return await self.repository.get_by_username(username)

    async def update_role(self, user: User, role: str) -> User:
        return await self.repository.update(db_obj=user, obj_in={"role": role})

    async def get_all_users(self, skip: int = 0, limit: int = 200) -> list:
        return await self.repository.get_multi(skip=skip, limit=limit)

from typing import Optional
from sqlalchemy import select, or_
from shared.base.repository import BaseRepository
from .models import User

class UserRepository(BaseRepository[User]):
    def __init__(self, db):
        super().__init__(User, db)

    async def get_by_email_or_login(self, identifier: str) -> Optional[User]:
        query = select(User).where(
            or_(User.email == identifier, User.login == identifier)
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def check_existence(self, email: str, login: str, username: str) -> Optional[User]:
        query = select(User).where(
            or_(
                User.email == email,
                User.login == login,
                User.username == username
            )
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_username(self, username: str) -> Optional[User]:
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)
        return result.scalars().first()

from typing import Optional
from sqlalchemy import select, or_
from app.repositories.base_repository import BaseRepository
from app.models.user import User

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

"""Репозиторий для доступа к данным пользователей в базе данных."""

from typing import Optional
from sqlalchemy import select, or_
from shared.base.repository import BaseRepository
from .models import User


class UserRepository(BaseRepository[User]):
    """Репозиторий операций с моделью User."""

    def __init__(self, db):
        """Инициализация репозитория пользователей.

        Args:
            db: Сессия SQLAlchemy.
        """
        super().__init__(User, db)

    async def get_by_email_or_login(self, identifier: str) -> Optional[User]:
        """Ищет пользователя по email или логину.

        Args:
            identifier: Email или логин пользователя.

        Returns:
            Экземпляр User или None, если пользователь не найден.
        """
        query = select(User).where(
            or_(User.email == identifier, User.login == identifier)
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def check_existence(self, email: str, login: str, username: str) -> Optional[User]:
        """Проверяет занятость любого из уникальных полей: email, login или username.

        Args:
            email: Email для проверки.
            login: Логин для проверки.
            username: Публичный никнейм для проверки.

        Returns:
            Существующий пользователь, у которого совпало одно из полей, либо None.
        """
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
        """Ищет пользователя по публичному никнейму (@username).

        Args:
            username: Имя пользователя.

        Returns:
            Экземпляр User или None, если пользователь не найден.
        """
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)
        return result.scalars().first()


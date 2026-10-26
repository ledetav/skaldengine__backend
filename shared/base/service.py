"""Базовый сервисный слой бизнес-логики."""

from typing import Generic, TypeVar

RepositoryType = TypeVar("RepositoryType")


class BaseService(Generic[RepositoryType]):
    """Базовый класс сервиса с внедрением репозитория."""

    def __init__(self, repository: RepositoryType):
        """Инициализация сервиса с экземпляром репозитория.

        Args:
            repository: Экземпляр репозитория для работы с данными.
        """
        self.repository = repository


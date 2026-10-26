from abc import ABC, abstractmethod
from typing import Any
from app.core.prompt_pipeline.context import PipelineContext


class PipelineStage(ABC):
    """Базовый абстрактный класс для этапа пайплайна сборки промпта."""

    @abstractmethod
    async def process(self, context: PipelineContext, user_text: str = "") -> Any:
        """
        Выполнить этап обработки контекста.
        :param context: Общее состояние пайплайна
        :param user_text: Входное сообщение пользователя
        """
        pass

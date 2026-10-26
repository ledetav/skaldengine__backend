from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.domains.chat.models import Chat
from app.domains.character.models import Character
from app.domains.persona.models import UserPersona
from app.domains.scenario.models import Scenario
from app.core.prompt_pipeline.context import PipelineContext
from app.core.prompt_pipeline.stages.base import PipelineStage


class IdentityStage(PipelineStage):
    """
    Этап 1: Сборка статического ядра.
    Загружает Chat, Character (с привязанными лорбуками), UserPersona и Scenario.
    """

    async def process(self, context: PipelineContext, user_text: str = "") -> None:
        result = await context.db.execute(
            select(Chat).where(Chat.id == context.chat_id)
        )
        context.chat = result.scalar_one_or_none()
        if not context.chat:
            raise ValueError(f"Chat {context.chat_id} not found")

        # Загружаем связанные объекты
        char_res = await context.db.execute(
            select(Character)
            .options(selectinload(Character.lorebooks))
            .where(Character.id == context.chat.character_id)
        )
        context.character = char_res.scalar_one_or_none()

        context.persona = await context.db.get(UserPersona, context.chat.user_persona_id)

        if context.chat.scenario_id:
            context.scenario = await context.db.get(Scenario, context.chat.scenario_id)

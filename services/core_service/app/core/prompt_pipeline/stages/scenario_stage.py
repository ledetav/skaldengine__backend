from sqlalchemy import select, and_

from app.domains.chat.models import ChatCheckpoint
from app.core.prompt_pipeline.context import PipelineContext
from app.core.prompt_pipeline.stages.base import PipelineStage


class ScenarioStage(PipelineStage):
    """
    Этап 4: Инъекция сценарного супервизора.
    Определяет текущую цель сценария и активирует критическое вмешательство при стагнации (messages_spent >= 8).
    """

    async def process(self, context: PipelineContext, user_text: str = "") -> None:
        if not context.chat or context.chat.mode != "scenario":
            return

        query = (
            select(ChatCheckpoint)
            .where(
                and_(
                    ChatCheckpoint.chat_id == context.chat_id,
                    ChatCheckpoint.is_completed == False
                )
            )
            .order_by(ChatCheckpoint.order_num.asc())
            .limit(1)
        )
        result = await context.db.execute(query)
        checkpoint = result.scalar_one_or_none()

        if checkpoint:
            base_goal = checkpoint.goal_description
            if checkpoint.messages_spent >= 8:
                context.scenario_directive = (
                    f"[CRITICAL NARRATIVE INTERVENTION]: The story has stalled for too long. "
                    f"Break the loop! You MUST immediately take a bold action or introduce a dramatic "
                    f"event to achieve this goal: [{base_goal}]. No more subtle guidance—make it happen NOW."
                )
            else:
                context.scenario_directive = (
                    f"CURRENT SCENARIO GOAL: {base_goal}. Subtly guide the dialogue towards this."
                )
        else:
            context.scenario_directive = "None. Narrative is driven by sandbox interactions."

from sqlalchemy import select, literal

from app.domains.chat.message_models import Message
from app.core.prompt_pipeline.context import PipelineContext
from app.core.prompt_pipeline.stages.base import PipelineStage


class HistoryStage(PipelineStage):
    """
    Этап 5: Реконструкция дерева истории сообщений.
    Использует рекурсивный CTE для выборки последних 20 сообщений от текущего листа
    и воссоздает теги <Internal_Analysis> для скрытых размышлений ассистента.
    """

    async def process(self, context: PipelineContext, user_text: str = "") -> None:
        if not context.chat:
            return

        current_id = context.parent_id or context.chat.active_leaf_id
        messages = []
        limit = 20

        if current_id:
            base_query = (
                select(Message.id, Message.parent_id, literal(1).label('depth'))
                .where(Message.id == current_id)
                .cte(name="history_tree", recursive=True)
            )
            recursive_query = (
                select(Message.id, Message.parent_id, (base_query.c.depth + 1).label('depth'))
                .join(base_query, Message.id == base_query.c.parent_id)
                .where(base_query.c.depth < limit)
            )
            cte = base_query.union_all(recursive_query)
            query = select(Message).join(cte, Message.id == cte.c.id).order_by(cte.c.depth.asc())
            result = await context.db.execute(query)
            messages = list(result.scalars().all())
            messages.reverse()

        for msg in messages:
            role = "user" if msg.role == "user" else "assistant"
            content_text = msg.content or ""
            if msg.role == "assistant" and msg.hidden_thought:
                content_text = f"<Internal_Analysis>{msg.hidden_thought}</Internal_Analysis>\n\n{content_text}"
            context.history.append({"role": role, "content": content_text})

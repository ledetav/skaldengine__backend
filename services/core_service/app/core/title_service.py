"""Сервис автоматической генерации названий для ролевых чатов."""

import uuid
from openai import AsyncOpenAI
from app.core.config import settings
from app.domains.chat.models import Chat


class ChatTitleService:
    """Сервис для анализа первого сообщения и генерации лаконичного названия истории."""

    def __init__(self):
        """Инициализация клиента OpenAI/Polza.ai."""
        self.client = AsyncOpenAI(
            base_url="https://polza.ai/api/v1",
            api_key=settings.POLZA_API_KEY
        )

    async def generate_and_update_title(self, chat_id: uuid.UUID, first_message: str):
        """Генерирует короткое название чата на основе первого сообщения пользователя

        и обновляет его в базе данных. Использует собственную асинхронную сессию БД
        для безопасного фонового выполнения.

        Args:
            chat_id: Идентификатор чата.
            first_message: Текст первого реплики пользователя.

        Returns:
            Сгенерированное название или None в случае ошибки.
        """
        from app.db.base import AsyncSessionLocal
        try:
            prompt = (
                "Summarize the following first message of a roleplay chat into a very short, "
                "engaging, thematic title (2 to 5 words maximum). "
                "Reply ONLY with the title itself, without quotes, prefixes, or punctuation at the end. "
                "Match the language of the message (Russian or English).\n\n"
                f"Message: {first_message[:500]}"
            )
            response = await self.client.chat.completions.create(
                model=settings.POLZA_TITLE_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=settings.POLZA_TITLE_MAX_TOKENS
            )
            title = response.choices[0].message.content.strip().strip('"').strip("'")
            if not title:
                return None

            async with AsyncSessionLocal() as db:
                chat = await db.get(Chat, chat_id)
                if chat:
                    chat.title = title[:100]
                    await db.commit()
                    return chat.title
        except Exception as e:
            print(f"[ERROR] Failed to generate chat title: {e}")
            return None

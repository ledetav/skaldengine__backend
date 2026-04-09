import uuid
from openai import AsyncOpenAI
from app.core.config import settings
from app.models.chat import Chat
from sqlalchemy.ext.asyncio import AsyncSession


class ChatTitleService:
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url="https://polza.ai/api/v1", 
            api_key=settings.POLZA_API_KEY
        )

    async def generate_and_update_title(self, db: AsyncSession, chat_id: uuid.UUID, first_message: str):
        """
        Генерирует короткое название чата на основе первого сообщения пользователя
        и обновляет его в базе данных.
        """
        try:
            prompt = (
                "Проанализируй первое сообщение пользователя в ролевом чате и придумай "
                "очень короткое, атмосферное название для этой истории (максимум 4-5 слов). "
                "Ответь ТОЛЬКО названием, без кавычек, вступлений и лишних слов.\n\n"
                f"Сообщение пользователя: {first_message}"
            )

            response = await self.client.chat.completions.create(
                model=settings.POLZA_TITLE_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=settings.POLZA_TITLE_MAX_TOKENS,
                temperature=0.7,
            )

            title = response.choices[0].message.content.strip()
            # Убираем кавычки если ИИ их добавил
            title = title.strip('"').strip("'")

            # Обновляем в БД
            chat = await db.get(Chat, chat_id)
            if chat:
                chat.title = title
                await db.commit()
                return title
        except Exception as e:
            print(f"[ERROR] Failed to generate chat title: {e}")
            return None

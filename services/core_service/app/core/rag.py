"""Модуль генерации векторных эмбеддингов и фоновой суммаризации истории чата (RAG)."""

import uuid
from openai import AsyncOpenAI
from sqlalchemy import select, literal_column
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings

# Экземпляр клиента Polza.ai по умолчанию
_default_client = AsyncOpenAI(base_url="https://polza.ai/api/v1", api_key=settings.POLZA_API_KEY)

EMPTY_FACTS_SENTINEL = "[NO_FACTS]"


async def get_embedding(text: str) -> list[float]:
    """Асинхронная генерация эмбеддинга (1536-dim) через text-embedding-3-small.

    Используется для сохранения фактов в эпизодическую память.

    Args:
        text: Текст факта для векторизации.

    Returns:
        Список чисел с плавающей точкой (вектор эмбеддинга).
    """
    client = AsyncOpenAI(base_url="https://polza.ai/api/v1", api_key=settings.POLZA_API_KEY)
    try:
        response = await client.embeddings.create(
            model=settings.POLZA_EMBEDDING_MODEL,
            input=text,
            dimensions=1536 if "text-embedding-3" in settings.POLZA_EMBEDDING_MODEL else None
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"[RAG] Error generating embedding: {e}")
        return []


async def get_query_embedding(query: str) -> list[float]:
    """Асинхронная генерация эмбеддинга для поискового запроса RAG.

    Args:
        query: Текст запроса для поиска релевантных воспоминаний.

    Returns:
        Вектор эмбеддинга запроса.
    """
    client = AsyncOpenAI(base_url="https://polza.ai/api/v1", api_key=settings.POLZA_API_KEY)
    try:
        response = await client.embeddings.create(
            model=settings.POLZA_EMBEDDING_MODEL,
            input=query,
            dimensions=1536 if "text-embedding-3" in settings.POLZA_EMBEDDING_MODEL else None
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"[RAG] Error generating query embedding: {e}")
        return []


async def process_sliding_window(db: AsyncSession, chat_id: uuid.UUID, leaf_id: uuid.UUID):
    """Фоновая обработка скользящего окна сообщений ветки чата.

    Извлекает сообщения, вышедшие за пределы оперативного контекста (последние 6 сообщений),
    выделяет из них ключевые факты с помощью LLM-суммаризатора и сохраняет векторные эмбеддинги
    в эпизодическую память (EpisodicMemory).

    Args:
        db: Асинхронная сессия базы данных.
        chat_id: Идентификатор чата.
        leaf_id: Идентификатор последнего листа текущей ветки сообщений.
    """
    from app.domains.chat.message_models import Message
    from app.domains.chat.models import EpisodicMemory

    # 1. Восстанавливаем полную ветку от корня до листа
    branch = []
    curr_id = leaf_id
    visited = set()
    while curr_id and curr_id not in visited:
        visited.add(curr_id)
        msg = await db.get(Message, curr_id)
        if not msg:
            break
        branch.append(msg)
        curr_id = msg.parent_id
    branch.reverse()

    if len(branch) <= 6:
        return  # Все сообщения помещаются в оперативное окно

    # Все сообщения, вышедшие за пределы окна последних 6
    fallen_out = branch[:-6]

    # Получаем идентификаторы сообщений этого чата, которые уже были суммаризированы
    res = await db.execute(select(EpisodicMemory.message_id).where(EpisodicMemory.chat_id == chat_id))
    summarized_ids = set(res.scalars().all())

    unsummarized = [m for m in fallen_out if m.id not in summarized_ids]
    if len(unsummarized) >= 4:
        chunk = unsummarized[:4]
        chunk_text = "\n".join([f"{m.role.upper()}: {m.content}" for m in chunk])
        target_msg_id = chunk[-1].id  # Привязываем память к последнему сообщению пачки

        prompt = f"""Extract 1 to 3 concrete, concise, standalone factual statements about events, decisions, revealed secrets, or character relationships from the following roleplay dialogue excerpt.
Focus on permanent plot points and character facts. Ignore trivial filler, greetings, or generic small talk.
If there are NO meaningful facts to remember, return an empty list: {{"facts": []}}.

Dialogue Excerpt:
{chunk_text}

Return ONLY a valid JSON object: {{"facts": ["fact 1", "fact 2"]}}
"""
        client = AsyncOpenAI(base_url="https://polza.ai/api/v1", api_key=settings.POLZA_API_KEY)
        try:
            response = await client.chat.completions.create(
                model=settings.POLZA_SUMMARY_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            import json
            data = json.loads(response.choices[0].message.content)
            facts = data.get("facts", [])

            saved_any = False
            for fact in facts:
                if fact and isinstance(fact, str) and fact.strip():
                    emb = await get_embedding(fact.strip())
                    if emb:
                        mem = EpisodicMemory(
                            chat_id=chat_id,
                            message_id=target_msg_id,
                            fact_content=fact.strip(),
                            embedding=emb
                        )
                        db.add(mem)
                        saved_any = True

            if not saved_any:
                # Помечаем чанк как обработанный сигнальным значением (sentinel), чтобы избежать повторной суммаризации
                dummy_vector = [0.0] * 1536
                dummy_vector[0] = 1.0
                sentinel_mem = EpisodicMemory(
                    chat_id=chat_id,
                    message_id=target_msg_id,
                    fact_content=EMPTY_FACTS_SENTINEL,
                    embedding=dummy_vector
                )
                db.add(sentinel_mem)

            await db.commit()
        except Exception as e:
            print(f"[RAG] Error in process_sliding_window: {e}")

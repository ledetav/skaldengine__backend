"""Модуль генерации векторных эмбеддингов и фоновой суммаризации истории чата (RAG)."""

import uuid
from typing import Optional, List
from openai import AsyncOpenAI
from sqlalchemy import select, desc, literal_column
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
    
    cte = select(
        Message.id, Message.parent_id, literal_column("1").label("depth")
    ).where(Message.id == leaf_id).cte(recursive=True)

    cte = cte.union_all(
        select(Message.id, Message.parent_id, (cte.c.depth + 1).label("depth"))
        .join(cte, Message.id == cte.c.parent_id)
        .where(cte.c.depth < 50)
    )

    query = select(Message).join(cte, Message.id == cte.c.id).order_by(cte.c.depth)
    res = await db.execute(query)
    branch = list(res.scalars().all())

    branch.reverse()
    
    # Оставляем последние 3 пары (6 сообщений) в оперативной памяти (вместе с промптом)
    if len(branch) <= 6:
        return
        
    # Все сообщения, вышедшие за пределы окна последних 6
    fallen_out = branch[:-6]
    
    # Получаем идентификаторы сообщений этого чата, которые уже были суммаризированы
    res = await db.execute(select(EpisodicMemory.message_id).where(EpisodicMemory.chat_id == chat_id))
    summarized_ids = set(res.scalars().all())
    
    unsummarized_chunk = []
    for msg in fallen_out:
        unsummarized_chunk.append(msg)
        if msg.id in summarized_ids:
            unsummarized_chunk.clear()
            
    # Проводим саммаризацию/векторизацию, когда накопилось 6 новых "выпавших" сообщений (~3 пары)
    if len(unsummarized_chunk) >= 6:
        chunk_to_process = unsummarized_chunk[:8]  # Берем до 8 сообщений для контекста
        
        dialogue = []
        for m in chunk_to_process:
            role = "Юзер" if m.role == "user" else "ИИ"
            dialogue.append(f"{role}: {m.content}")
        text_block = "\n".join(dialogue)
        
        prompt = f"""Проанализируй этот фрагмент диалога. Извлеки только новые, важные факты, значимые зацепки для сюжета, информацию о персонажах или изменения в их отношениях.
Верни ответ СТРОГО в формате JSON: {{"facts": ["факт 1", "факт 2", ...]}}.
Если ничего важного нет, верни {{"facts": []}}.
Игнорируй пустую болтовню. Пиши факты от 3-го лица, максимально лаконично и конкретно.

Диалог:
{text_block}
"""
        
        try:
            client = AsyncOpenAI(base_url="https://polza.ai/api/v1", api_key=settings.POLZA_API_KEY)
            response = await client.chat.completions.create(
                model=settings.POLZA_SUMMARY_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            
            import json
            raw_content = response.choices[0].message.content
            try:
                data = json.loads(raw_content)
                facts = data.get("facts", [])
            except json.JSONDecodeError:
                facts = []
            
            saved_any = False
            for fact_text in facts:
                if not isinstance(fact_text, str):
                    continue
                clean_fact = fact_text.strip()
                if not clean_fact:
                    continue
                    
                embedding = await get_embedding(clean_fact)
                if embedding:
                    mem = EpisodicMemory(
                        chat_id=chat_id,
                        message_id=chunk_to_process[-1].id,
                        summary=clean_fact,
                        embedding=embedding
                    )
                    db.add(mem)
                    saved_any = True
            
            if not saved_any:
                # Помечаем чанк как обработанный сигнальным значением (sentinel), чтобы избежать повторной суммаризации
                dummy_vector = [0.0] * 1536
                dummy_vector[0] = 1.0
                sentinel_mem = EpisodicMemory(
                    chat_id=chat_id,
                    message_id=chunk_to_process[-1].id,
                    summary=EMPTY_FACTS_SENTINEL,
                    embedding=dummy_vector
                )
                db.add(sentinel_mem)

            await db.commit()
        except Exception as e:
            print(f"[RAG] Error in process_sliding_window: {e}")


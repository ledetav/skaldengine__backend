import uuid
from typing import Optional, List
from openai import AsyncOpenAI
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings

# Polza client (OpenAI wrapper) default instance
_default_client = AsyncOpenAI(base_url="https://polza.ai/api/v1", api_key=settings.POLZA_API_KEY)


async def get_embedding(text: str, api_key: Optional[str] = None) -> list[float]:
    """
    Асинхронная генерация эмбеддинга (1536-dim) через text-embedding-3-small.
    Используется для сохранения воспоминаний.
    """
    client = AsyncOpenAI(base_url="https://polza.ai/api/v1", api_key=api_key) if api_key else _default_client
    try:
        response = await client.embeddings.create(
            model=settings.POLZA_EMBEDDING_MODEL,
            input=text
        )
        # text-embedding-3-small is typically 1536 dim, but to match 768 you'd need the dimensions parameter if supported
        # Assuming we just return it
        return response.data[0].embedding
    except Exception as e:
        print(f"[RAG] Error generating embedding: {e}")
        return []


async def get_query_embedding(query: str, api_key: Optional[str] = None) -> list[float]:
    """
    Асинхронная генерация эмбеддинга для поискового запроса.
    """
    client = AsyncOpenAI(base_url="https://polza.ai/api/v1", api_key=api_key) if api_key else _default_client
    try:
        response = await client.embeddings.create(
            model=settings.POLZA_EMBEDDING_MODEL,
            input=query
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"[RAG] Error generating query embedding: {e}")
        return []


async def process_sliding_window(db: AsyncSession, chat_id: uuid.UUID, leaf_id: uuid.UUID, api_key: Optional[str] = None):
    from app.domains.chat.message_models import Message
    from app.domains.chat.models import EpisodicMemory
    
    current_id = leaf_id
    branch = []
    while current_id and len(branch) < 50:
        msg = await db.get(Message, current_id)
        if not msg:
            break
        branch.append(msg)
        current_id = msg.parent_id
        
    branch.reverse()
    
    # Keep last 15 in working memory
    if len(branch) <= 15:
        return
        
    fallen_out = branch[:-15]
    
    # Retrieve all message_ids from this chat that were already summarized
    res = await db.execute(select(EpisodicMemory.message_id).where(EpisodicMemory.chat_id == chat_id))
    summarized_ids = set(res.scalars().all())
    
    unsummarized_chunk = []
    for msg in fallen_out:
        unsummarized_chunk.append(msg)
        if msg.id in summarized_ids:
            unsummarized_chunk.clear()
            
    if len(unsummarized_chunk) >= 4:
        chunk_to_process = unsummarized_chunk[:6]
        
        dialogue = []
        for m in chunk_to_process:
            role = "Юзер" if m.role == "user" else "ИИ"
            dialogue.append(f"{role}: {m.content}")
        text_block = "\n".join(dialogue)
        
        prompt = f"""Проанализируй этот фрагмент диалога. Извлеки только новые, важные факты, значимые действия или изменения в отношениях.
Игнорируй пустую болтовню, эмоции ради эмоций и описания погоды.
Формат ответа: массив кратких предложений от 3-го лица.

Диалог:
{text_block}
"""
        
        try:
            client = AsyncOpenAI(base_url="https://polza.ai/api/v1", api_key=api_key) if api_key else _default_client
            response = await client.chat.completions.create(
                model=settings.POLZA_SUMMARY_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            # Extracted facts
            response_text = response.choices[0].message.content
            lines = [line.strip() for line in response_text.split('\n') if line.strip()]
            summary = " ".join([line for line in lines if not line.startswith("Сгенерированный факт")])
            
            if summary:
                embedding = await get_embedding(summary, api_key=api_key)
                if embedding:
                    mem = EpisodicMemory(
                        chat_id=chat_id,
                        message_id=chunk_to_process[-1].id,
                        summary=summary,
                        embedding=embedding
                    )
                    db.add(mem)
                    await db.commit()
        except Exception as e:
            print(f"[RAG] Error in process_sliding_window: {e}")

"""
RAG (Retrieval Augmented Generation) module.
Updated for async support and pgvector integration.
"""
from google import genai
from google.genai import types
from app.core.config import settings

# Gemini client
client = genai.Client(api_key=settings.GEMINI_API_KEY)


async def get_embedding(text: str) -> list[float]:
    """
    Асинхронная генерация эмбеддинга (768-dim) через text-embedding-004.
    Используется для сохранения воспоминаний.
    """
    try:
        response = await client.aio.models.embed_content(
            model="text-embedding-004",
            contents=text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=768,
            )
        )
        return response.embeddings[0].values
    except Exception as e:
        print(f"[RAG] Error generating embedding: {e}")
        return []


async def get_query_embedding(query: str) -> list[float]:
    """
    Асинхронная генерация эмбеддинга для поискового запроса.
    """
    try:
        response = await client.aio.models.embed_content(
            model="text-embedding-004",
            contents=query,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=768,
            )
        )
        return response.embeddings[0].values
    except Exception as e:
        print(f"[RAG] Error generating query embedding: {e}")
        return []


async def process_sliding_window(db: "AsyncSession", chat_id: "uuid.UUID", leaf_id: "uuid.UUID"):
    import uuid
    from app.models.message import Message
    from app.models.episodic_memory import EpisodicMemory
    from sqlalchemy import select
    
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
            response = await client.aio.models.generate_content(
                model="gemini-3-flash-lite-preview",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3
                )
            )
            # Extracted facts
            lines = [line.strip() for line in response.text.split('\n') if line.strip()]
            summary = " ".join([line for line in lines if not line.startswith("Сгенерированный факт")])
            
            if summary:
                embedding = await get_embedding(summary)
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
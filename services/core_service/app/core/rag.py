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
"""
RAG (Retrieval Augmented Generation) module.

MIGRATION NOTE: ChromaDB removed. Vector search now uses pgvector (EpisodicMemory table).
This module will be rewritten in blocks 3-6 of the architecture redesign.
"""
from google import genai
from google.genai import types
from app.core.config import settings

# Gemini client (shared across the app)
client = genai.Client(api_key=settings.GEMINI_API_KEY)


def generate_embedding(text: str) -> list[float]:
    """
    Generates a 768-dim embedding vector via Gemini gemini-embedding-001.
    Used for episodic memory storage and retrieval.
    """
    try:
        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
            )
        )
        return response.embeddings[0].values
    except Exception as e:
        print(f"[RAG] Error generating embedding: {e}")
        return []


def generate_query_embedding(query: str) -> list[float]:
    """
    Generates a query embedding (task_type=RETRIEVAL_QUERY) for semantic search.
    """
    try:
        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=query,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY"
            )
        )
        return response.embeddings[0].values
    except Exception as e:
        print(f"[RAG] Error generating query embedding: {e}")
        return []
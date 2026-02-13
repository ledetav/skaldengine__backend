import chromadb
from google import genai
from google.genai import types
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings
from app.models.lore_item import LoreItem

client = genai.Client(api_key=settings.GEMINI_API_KEY)

chroma_client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
lore_collection = chroma_client.get_or_create_collection(name="character_lore")

def generate_embedding(text: str) -> list[float]:
    """
    Превращает текст в вектор чисел с помощью модели Google gemini-embedding-001.
    """
    try:
        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                title="Lore Item" # Title нужен только для task_type=RETRIEVAL_DOCUMENT
            )
        )
        return response.embeddings[0].values
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return []

def index_lore_item(lore_item: LoreItem):
    """
    Сохраняет факт в ChromaDB.
    """
    if not lore_item.content:
        return

    embedding = generate_embedding(lore_item.content)
    if not embedding:
        print(f"⚠️ Failed to generate embedding for lore {lore_item.id}")
        return

    lore_collection.upsert(
        ids=[str(lore_item.id)],
        embeddings=[embedding],
        documents=[lore_item.content],
        metadatas=[{
            "character_id": str(lore_item.character_id),
            "category": lore_item.category
        }]
    )
    print(f"✅ Indexed lore item: {lore_item.id}")

def delete_lore_from_index(lore_item_id: str):
    """
    Удаляет факт из векторной базы.
    """
    try:
        lore_collection.delete(ids=[lore_item_id])
        print(f"🗑️ Deleted lore item from index: {lore_item_id}")
    except Exception as e:
        print(f"Error deleting from index: {e}")

def search_relevant_lore(query: str, character_id: str, k: int = 3) -> list[str]:
    """
    Ищет топ-K самых похожих фактов для конкретного персонажа.
    """
    try:
        # Для запроса используем task_type="RETRIEVAL_QUERY" и НЕ указываем title
        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=query,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY"
            )
        )
        query_embedding = response.embeddings[0].values

        results = lore_collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where={"character_id": character_id} 
        )

        if results and results['documents']:
            return results['documents'][0] 
        return []
    except Exception as e:
        print(f"Error searching lore: {e}")
        return []
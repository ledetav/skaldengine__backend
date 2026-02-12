import chromadb
import google.generativeai as genai
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings
from app.models.lore_item import LoreItem

genai.configure(api_key=settings.GEMINI_API_KEY)

chroma_client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)

lore_collection = chroma_client.get_or_create_collection(name="character_lore")

def generate_embedding(text: str) -> list[float]:
    """
    Превращает текст в вектор чисел с помощью модели Google text-embedding-004.
    """
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document",
            title="Lore Item"
        )
        return result['embedding']
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
    lore_collection.delete(ids=[lore_item_id])
    print(f"🗑️ Deleted lore item from index: {lore_item_id}")

def search_relevant_lore(query: str, character_id: str, k: int = 3) -> list[str]:
    """
    Ищет топ-K самых похожих фактов для конкретного персонажа.
    """
    query_embedding = genai.embed_content(
        model="models/text-embedding-004",
        content=query,
        task_type="retrieval_query"
    )['embedding']

    results = lore_collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        where={"character_id": character_id} 
    )

    if results and results['documents']:
        return results['documents'][0]
    return []
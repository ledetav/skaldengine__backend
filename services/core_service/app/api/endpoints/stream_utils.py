import json
import re
from uuid import UUID
from google import genai
from app.core.config import settings

_client = genai.Client(api_key=settings.GEMINI_API_KEY)

async def generate_chat_stream(
    ai_msg_id: UUID, 
    payload: dict,
    state: dict
):
    """
    Асинхронный генератор для SSE.
    state - словарь для передачи полного текста в фоновую задачу.
    """
    # Yield ID сообщения
    yield f"event: message_id\ncontent-type: application/json\ndata: {json.dumps({'id': str(ai_msg_id)})}\n\n"

    full_text = ""
    try:
        response_stream = await _client.aio.models.generate_content_stream(
            model="gemini-2.0-flash",
            contents=payload["contents"],
            config=payload["config"]
        )
        
        async for chunk in response_stream:
            text_chunk = chunk.text or ""
            if text_chunk:
                full_text += text_chunk
                yield f"event: token\ndata: {json.dumps({'text': text_chunk})}\n\n"
            
    except Exception as e:
        error_msg = "(System Error: Neural network unavailable)"
        yield f"event: token\ndata: {json.dumps({'text': error_msg})}\n\n"
        full_text += error_msg

    # Окончание стрима
    yield f"event: done\ndata: {json.dumps({'status': 'success'})}\n\n"
    
    # Сохраняем полный текст для фоновой задачи
    state["full_text"] = full_text

async def process_post_generation(chat_id: UUID, ai_msg_id: UUID, state: dict):
    from app.db.base import AsyncSessionLocal
    from app.models.message import Message
    from app.models.chat_checkpoint import ChatCheckpoint
    from sqlalchemy import select
    from app.core import rag
    from app.core.director_service import DirectorService
    
    full_text = state.get("full_text", "")
    if not full_text: 
        return
    
    thought_match = re.search(r"<Internal_Analysis>(.*?)</Internal_Analysis>", full_text, flags=re.DOTALL)
    if thought_match:
        hidden_thought = thought_match.group(1).strip()
        ai_text = re.sub(r"<Internal_Analysis>.*?</Internal_Analysis>", "", full_text, flags=re.DOTALL).strip()
    else:
        hidden_thought = None
        ai_text = full_text.strip()
        
    async with AsyncSessionLocal() as db:
        ai_msg = await db.get(Message, ai_msg_id)
        if not ai_msg:
            return
            
        ai_msg.content = ai_text
        ai_msg.hidden_thought = hidden_thought
        db.add(ai_msg)
        await db.commit()
        
        # 1. RAG Memory
        try:
            if ai_msg.parent_id:
                user_msg = await db.get(Message, ai_msg.parent_id)
                if user_msg:
                    # add_to_memory signature in earlier code implied it took db, chat_id, user_content, ai_content
                    # We'll just run it with our db session
                    await rag.add_to_memory(db, chat_id, user_msg.content, ai_text)
                    await db.commit()
        except Exception as e:
            print(f"[RAG] Error adding to memory: {e}")
            
        # 2. Supervisor check
        try:
            res = await db.execute(
                select(ChatCheckpoint)
                .where(ChatCheckpoint.chat_id == chat_id, ChatCheckpoint.is_completed == False)
                .order_by(ChatCheckpoint.order_num)
            )
            checkpoint = res.scalars().first()
            if checkpoint and checkpoint.messages_spent > 0 and checkpoint.messages_spent % 3 == 0:
                director = DirectorService()
                await director.check_progress(chat_id)
        except Exception as e:
            print(f"[Supervisor] Error checking progress: {e}")

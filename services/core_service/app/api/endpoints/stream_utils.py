import json
import re
from uuid import UUID
from openai import AsyncOpenAI
from app.core.config import settings

_client = AsyncOpenAI(base_url="https://polza.ai/api/v1", api_key=settings.POLZA_API_KEY)

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
    yield f"event: message_id\ndata: {json.dumps({'id': str(ai_msg_id)}, ensure_ascii=False)}\n\n"

    full_text = ""
    is_thinking = False
    buffer = ""

    try:
        response_stream = await _client.chat.completions.create(**payload)
        
        async for chunk in response_stream:
            if chunk.choices and len(chunk.choices) > 0:
                text_chunk = chunk.choices[0].delta.content or ""
                if not text_chunk:
                    continue
                
                full_text += text_chunk
                buffer += text_chunk
                
                # Logic to hide everything between <Internal_Analysis> and </Internal_Analysis>
                while True:
                    if not is_thinking:
                        if "<Internal_Analysis>" in buffer:
                            # Start thinking: send everything BEFORE the tag
                            pre_thought, post_tag = buffer.split("<Internal_Analysis>", 1)
                            if pre_thought:
                                yield f"event: token\ndata: {json.dumps({'text': pre_thought}, ensure_ascii=False)}\n\n"
                            buffer = post_tag
                            is_thinking = True
                        else:
                            # Not thinking and no tag yet: send the whole buffer
                            yield f"event: token\ndata: {json.dumps({'text': buffer}, ensure_ascii=False)}\n\n"
                            buffer = ""
                            break
                    else:
                        if "</Internal_Analysis>" in buffer:
                            # End thinking: discard everything until end tag, then continue
                            _, post_thought = buffer.split("</Internal_Analysis>", 1)
                            buffer = post_thought
                            is_thinking = False
                        else:
                            # Still thinking: keep buffering, but we only need to keep 
                            # the last few characters to catch the tag if it's split.
                            if len(buffer) > 30:
                                buffer = buffer[-30:]
                            break
            
    except Exception as e:
        error_msg = "(System Error: Neural network unavailable)"
        yield f"event: token\ndata: {json.dumps({'text': error_msg}, ensure_ascii=False)}\n\n"
        full_text += error_msg

    # Окончание стрима
    yield f"event: done\ndata: {json.dumps({'status': 'success'}, ensure_ascii=False)}\n\n"
    
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
        
        # 1. RAG Memory (Sliding Window Ingestion)
        try:
            await rag.process_sliding_window(db, chat_id, ai_msg_id)
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

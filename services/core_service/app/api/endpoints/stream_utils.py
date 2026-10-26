import json
import re
import asyncio
from uuid import UUID
from openai import AsyncOpenAI
from app.core.config import settings

_client = AsyncOpenAI(base_url="https://polza.ai/api/v1", api_key=settings.POLZA_API_KEY)

async def generate_chat_stream(
    chat_id: UUID,
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
        api_key = state.get("polza_api_key") or settings.POLZA_API_KEY
        client = AsyncOpenAI(base_url="https://polza.ai/api/v1", api_key=api_key)
        response_stream = await client.chat.completions.create(**payload)
        
        async for chunk in response_stream:
            if chunk.choices and len(chunk.choices) > 0:
                text_chunk = chunk.choices[0].delta.content or ""
                if not text_chunk:
                    continue
                
                full_text += text_chunk
                buffer += text_chunk
                
                START_TAG = "<Internal_Analysis>"
                END_TAG = "</Internal_Analysis>"
                
                # Logic to hide everything between <Internal_Analysis> and </Internal_Analysis>
                while buffer:
                    if not is_thinking:
                        if START_TAG in buffer:
                            # Start thinking: send everything BEFORE the tag
                            pre_thought, post_tag = buffer.split(START_TAG, 1)
                            if pre_thought:
                                yield f"event: token\ndata: {json.dumps({'content': pre_thought}, ensure_ascii=False)}\n\n"
                            buffer = post_tag
                            is_thinking = True
                        else:
                            # Check if the end of buffer might be the beginning of START_TAG
                            matching_prefix_len = 0
                            max_check = min(len(buffer), len(START_TAG) - 1)
                            for k in range(max_check, 0, -1):
                                if buffer.endswith(START_TAG[:k]):
                                    matching_prefix_len = k
                                    break
                            
                            if matching_prefix_len > 0:
                                # Send everything up to the matching prefix, keep prefix in buffer
                                to_emit = buffer[:-matching_prefix_len]
                                if to_emit:
                                    yield f"event: token\ndata: {json.dumps({'content': to_emit}, ensure_ascii=False)}\n\n"
                                buffer = buffer[-matching_prefix_len:]
                                break
                            else:
                                # No partial match: emit the entire buffer
                                yield f"event: token\ndata: {json.dumps({'content': buffer}, ensure_ascii=False)}\n\n"
                                buffer = ""
                                break
                    else:
                        if END_TAG in buffer:
                            # End thinking: discard everything until end tag, then continue
                            _, post_thought = buffer.split(END_TAG, 1)
                            buffer = post_thought
                            is_thinking = False
                        else:
                            # Still thinking: keep only enough characters to detect END_TAG if split
                            if len(buffer) > len(END_TAG) - 1:
                                buffer = buffer[-(len(END_TAG) - 1):]
                            break
            
        # Flush any remaining buffer if stream finished and we are not thinking
        if not is_thinking and buffer:
            yield f"event: token\ndata: {json.dumps({'content': buffer}, ensure_ascii=False)}\n\n"
            buffer = ""

    except Exception as e:
        error_msg = "(System Error: Neural network unavailable)"
        yield f"event: token\ndata: {json.dumps({'content': error_msg}, ensure_ascii=False)}\n\n"
        full_text += error_msg

    # Окончание стрима
    yield f"event: done\ndata: {json.dumps({'status': 'success'}, ensure_ascii=False)}\n\n"
    
    # Сохраняем полный текст для фоновой задачи
    state["full_text"] = full_text
    asyncio.create_task(process_post_generation(chat_id, ai_msg_id, state))

async def process_post_generation(chat_id: UUID, ai_msg_id: UUID, state: dict):
    from app.db.base import AsyncSessionLocal
    from app.domains.chat.message_models import Message
    from app.domains.chat.models import ChatCheckpoint
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
            api_key = state.get("polza_api_key")
            await rag.process_sliding_window(db, chat_id, ai_msg_id, api_key=api_key)
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
                director = DirectorService(api_key=api_key)
                await director.check_progress(chat_id, leaf_id=ai_msg_id, api_key=api_key)
        except Exception as e:
            print(f"[Supervisor] Error checking progress: {e}")

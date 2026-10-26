"""Утилиты для потоковой передачи ответов нейросети (SSE) и пост-обработки сообщений."""

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
    """Асинхронный генератор событий Server-Sent Events (SSE).

    Выполняет потоковую генерацию ответа через Polza.ai, скрывая от пользователя
    внутренний блок размышлений <Internal_Analysis>...</Internal_Analysis>.

    Args:
        chat_id: Идентификатор чата.
        ai_msg_id: Идентификатор генерируемого сообщения ассистента.
        payload: Параметры запроса к модели (OpenAI Chat Completions).
        state: Словарь для передачи накопленного полного текста в фоновую задачу.
    """
    # Отправка события ID сообщения
    yield f"event: message_id\ndata: {json.dumps({'id': str(ai_msg_id)}, ensure_ascii=False)}\n\n"

    full_text = ""
    is_thinking = False
    buffer = ""

    try:
        client = AsyncOpenAI(base_url="https://polza.ai/api/v1", api_key=settings.POLZA_API_KEY)
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
                
                # Логика скрытия содержимого между тегами <Internal_Analysis> и </Internal_Analysis>
                while buffer:
                    if not is_thinking:
                        if START_TAG in buffer:
                            # Начало блока размышлений: отправляем всё ДО тега
                            pre_thought, post_tag = buffer.split(START_TAG, 1)
                            if pre_thought:
                                yield f"event: token\ndata: {json.dumps({'content': pre_thought}, ensure_ascii=False)}\n\n"
                            buffer = post_tag
                            is_thinking = True
                        else:
                            # Проверяем, может ли хвост буфера быть началом START_TAG
                            matching_prefix_len = 0
                            max_check = min(len(buffer), len(START_TAG) - 1)
                            for k in range(max_check, 0, -1):
                                if buffer.endswith(START_TAG[:k]):
                                    matching_prefix_len = k
                                    break
                            
                            if matching_prefix_len > 0:
                                # Отправляем всё до совпадающего префикса, оставляя префикс в буфере
                                to_emit = buffer[:-matching_prefix_len]
                                if to_emit:
                                    yield f"event: token\ndata: {json.dumps({'content': to_emit}, ensure_ascii=False)}\n\n"
                                buffer = buffer[-matching_prefix_len:]
                                break
                            else:
                                # Частичного совпадения нет: отдаем весь буфер
                                yield f"event: token\ndata: {json.dumps({'content': buffer}, ensure_ascii=False)}\n\n"
                                buffer = ""
                                break
                    else:
                        if END_TAG in buffer:
                            # Конец размышлений: отбрасываем блок размышлений и продолжаем
                            _, post_thought = buffer.split(END_TAG, 1)
                            buffer = post_thought
                            is_thinking = False
                        else:
                            # Всё еще в блоке размышлений: держим в буфере только символы для детекции END_TAG
                            if len(buffer) > len(END_TAG) - 1:
                                buffer = buffer[-(len(END_TAG) - 1):]
                            break
            
        # Сбрасываем остаток буфера по завершении потока, если не в блоке размышлений
        if not is_thinking and buffer:
            yield f"event: token\ndata: {json.dumps({'content': buffer}, ensure_ascii=False)}\n\n"
            buffer = ""

    except Exception as e:
        error_msg = "(Системная ошибка: нейросеть временно недоступна)"
        yield f"event: token\ndata: {json.dumps({'content': error_msg}, ensure_ascii=False)}\n\n"
        full_text += error_msg

    # Окончание стрима
    yield f"event: done\ndata: {json.dumps({'status': 'success'}, ensure_ascii=False)}\n\n"
    
    # Сохраняем полный текст для фоновой задачи
    state["full_text"] = full_text
    asyncio.create_task(process_post_generation(chat_id, ai_msg_id, state))


async def process_post_generation(chat_id: UUID, ai_msg_id: UUID, state: dict):
    """Фоновая пост-обработка сгенерированного сообщения.

    Сохраняет чистый текст ответа и скрытые мысли в БД, запускает фоновую суммаризацию
    памяти RAG и инициирует периодическую проверку прогресса сценария супервайзером.

    Args:
        chat_id: Идентификатор чата.
        ai_msg_id: Идентификатор сообщения ИИ.
        state: Словарь состояния с полным текстом генерации.
    """
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
        
        # 1. Эпизодическая память RAG (обработка скользящего окна)
        try:
            await rag.process_sliding_window(db, chat_id, ai_msg_id)
        except Exception as e:
            print(f"[RAG] Error adding to memory: {e}")
            
        # 2. Проверка прогресса сценария супервайзером
        try:
            res = await db.execute(
                select(ChatCheckpoint)
                .where(ChatCheckpoint.chat_id == chat_id, ChatCheckpoint.is_completed == False)
                .order_by(ChatCheckpoint.order_num)
            )
            checkpoint = res.scalars().first()
            if checkpoint and checkpoint.messages_spent > 0 and checkpoint.messages_spent % 3 == 0:
                director = DirectorService()
                await director.check_progress(chat_id, leaf_id=ai_msg_id)
        except Exception as e:
            print(f"[Supervisor] Error checking progress: {e}")


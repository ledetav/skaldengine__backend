from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update as sa_update
import json
from pydantic import BaseModel

from app.api import deps
from app.models.message import Message
from app.models.chat import Chat
from app.schemas.message import Message as MessageSchema
from app.core.prompt_pipeline import PromptPipeline
from app.api.endpoints.stream_utils import generate_chat_stream

router = APIRouter()

class MessageEdit(BaseModel):
    new_content: str


# ─── Хелпер: атомарно обновляем active_leaf_id через прямой UPDATE ─────── #

async def _set_active_leaf(db: AsyncSession, chat_id: UUID, msg_id: UUID) -> None:
    """Надёжно выставляет active_leaf_id в обход ORM-кэша и post_update."""
    await db.execute(
        sa_update(Chat)
        .where(Chat.id == chat_id)
        .values(active_leaf_id=msg_id)
    )


# ─── Регенерация ответа (свайп) ──────────────────────────────────────────── #

@router.post("/{parent_id}/regenerate/stream")
async def regenerate_message_stream(
    parent_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """
    Генерирует альтернативный ответ (Свайп).
    Создает новую ветку сообщения ИИ от указанного сообщения пользователя (parent_id).
    """
    parent_msg = await db.get(Message, parent_id)
    if not parent_msg or parent_msg.role != "user":
        raise HTTPException(status_code=404, detail="Parent user message not found")
        
    chat = await db.get(Chat, parent_msg.chat_id)
    if not chat or str(chat.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Chat not found")

    # Сборка промпта (передаем parent_id, чтобы история обрезалась по нему)
    pipeline = PromptPipeline(db, chat.id, current_user=current_user, parent_id=parent_id)
    payload = await pipeline.build_payload(parent_msg.content)
    
    # Создаем "пустое" сообщение ИИ
    ai_msg = Message(
        chat_id=chat.id,
        role="assistant",
        content="",
        parent_id=parent_id,
    )
    db.add(ai_msg)
    await db.flush()  # Получаем ai_msg.id до commit

    # Обновляем active_leaf_id напрямую через SQL (обходим post_update баг)
    await _set_active_leaf(db, chat.id, ai_msg.id)
    await db.commit()
    await db.refresh(ai_msg)

    # Запускаем стриминг
    state = {}
    generator = generate_chat_stream(chat.id, ai_msg.id, payload, state)

    return StreamingResponse(generator, media_type="text/event-stream")


# ─── Редактирование сообщения (создание новой ветки) ─────────────────────── #

@router.put("/{message_id}", response_model=MessageSchema)
async def edit_message(
    message_id: UUID,
    message_in: MessageEdit,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """
    Редактирование истории (Ответвление).
    Создает дубликат сообщения с новым текстом (is_edited=True).
    Возвращает новую сущность. Фронтенд после этого может вызвать regenerate (если это сообщение юзера).
    """
    original_msg = await db.get(Message, message_id)
    if not original_msg:
        raise HTTPException(status_code=404, detail="Message not found")
        
    chat = await db.get(Chat, original_msg.chat_id)
    if not chat or str(chat.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Chat not found")
        
    new_msg = Message(
        chat_id=chat.id,
        role=original_msg.role,
        content=message_in.new_content,
        parent_id=original_msg.parent_id,
        is_edited=True
    )
    db.add(new_msg)
    await db.flush()  # Получаем new_msg.id до commit

    # Обновляем active_leaf_id напрямую через SQL
    await _set_active_leaf(db, chat.id, new_msg.id)
    await db.commit()
    await db.refresh(new_msg)
    
    return new_msg

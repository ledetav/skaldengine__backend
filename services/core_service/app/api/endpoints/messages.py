from typing import cast, List, Optional
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
from app.schemas.chat import Chat as ChatSchemaRes
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
    Редактирование истории (Непрямое ветвление).
    Создает дубликат сообщения с новым текстом (is_edited=True).
    Возвращает новую сущность. Оригинал остается в дереве для свайпов.
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
    await db.flush()

    await _set_active_leaf(db, chat.id, new_msg.id)
    await db.commit()
    await db.refresh(new_msg)
    
    return new_msg


# ─── Явное ветвление (Создание нового чата-форка) ─────────────────────────── #

@router.post("/{message_id}/fork", response_model=ChatSchemaRes)
async def fork_chat_at(
    message_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """
    Явное ветвление (Форк в новый чат).
    Создает ПОЛНУЮ КОПИЮ текущего чата в новом объекте, обрезая историю по выбранному сообщению.
    Оригинальный чат остается НЕИЗМЕННЫМ. 
    Новый чат получает:
    1. Все сообщения от начала до выбранного.
    2. Все факты памяти (RAG), привязанные к этим сообщениям.
    3. Состояние сценария (чекпоинты).
    """
    from app.models.episodic_memory import EpisodicMemory
    from app.models.chat_checkpoint import ChatCheckpoint

    target_msg = await db.get(Message, message_id)
    if not target_msg or not isinstance(target_msg, Message):
        raise HTTPException(status_code=404, detail="Message not found")
    target_msg = cast(Message, target_msg)
        
    original_chat_obj = await db.get(Chat, target_msg.chat_id)
    if not original_chat_obj or not isinstance(original_chat_obj, Chat):
        raise HTTPException(status_code=404, detail="Chat not found")
    original_chat_obj = cast(Chat, original_chat_obj)
    
    if str(original_chat_obj.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Forbidden")

    # 1. Создаем НОВЫЙ ЧАТ (клонируем настройки)
    new_chat = Chat(
        user_id=current_user.id,
        character_id=original_chat_obj.character_id,
        user_persona_id=original_chat_obj.user_persona_id,
        mode=original_chat_obj.mode,
        scenario_id=original_chat_obj.scenario_id,
        is_acquainted=original_chat_obj.is_acquainted,
        relationship_dynamic=original_chat_obj.relationship_dynamic,
        language=original_chat_obj.language,
        narrative_voice=original_chat_obj.narrative_voice,
        persona_lorebook_id=original_chat_obj.persona_lorebook_id
    )
    db.add(new_chat)
    await db.flush()

    # 2. Выстраиваем путь предков: от корня до выбранного сообщения
    ancestor_path: list[Message] = []
    curr_msg: Message | None = target_msg
    while curr_msg is not None:
        ancestor_path.append(curr_msg)
        if curr_msg.parent_id is None: 
            break
        # Получаем родителя
        res = await db.execute(select(Message).where(Message.id == curr_msg.parent_id))
        curr_msg = res.scalar_one_or_none()
    
    ancestor_path.reverse() # Теперь: [root, ..., target]

    # 3. Клонируем сообщения в новый чат
    old_to_new_msg_map = {}
    last_new_parent_id = None
    
    for old_msg in ancestor_path:
        cloned_msg = Message(
            chat_id=new_chat.id,
            role=old_msg.role,
            content=old_msg.content,
            hidden_thought=old_msg.hidden_thought,
            is_edited=old_msg.is_edited,
            parent_id=last_new_parent_id,
            created_at=old_msg.created_at
        )
        db.add(cloned_msg)
        await db.flush()
        old_to_new_msg_map[old_msg.id] = cloned_msg.id
        last_new_parent_id = cloned_msg.id

    # 4. Устанавливаем активны лист в новом чате
    new_chat.active_leaf_id = last_new_parent_id

    # 5. Клонируем RAG-память (Эпизодическую)
    mem_res = await db.execute(
        select(EpisodicMemory).where(EpisodicMemory.message_id.in_(old_to_new_msg_map.keys()))
    )
    for old_mem in mem_res.scalars().all():
        new_mem = EpisodicMemory(
            chat_id=new_chat.id,
            message_id=old_to_new_msg_map[old_mem.message_id],
            summary=old_mem.summary,
            embedding=old_mem.embedding
        )
        db.add(new_mem)

    # 6. Клонируем чекпоинты (если сценарий)
    if original_chat_obj.mode == "scenario":
        cp_res = await db.execute(select(ChatCheckpoint).where(ChatCheckpoint.chat_id == original_chat_obj.id))
        for old_cp in cp_res.scalars().all():
            new_cp = ChatCheckpoint(
                chat_id=new_chat.id,
                order_num=old_cp.order_num,
                goal_description=old_cp.goal_description,
                is_completed=old_cp.is_completed,
                messages_spent=old_cp.messages_spent
            )
            db.add(new_cp)

    await db.commit()
    await db.refresh(new_chat)
    
    return new_chat

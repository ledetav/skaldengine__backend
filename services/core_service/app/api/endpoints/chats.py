from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update as sa_update

from app.api import deps
from app.core.config import settings
from app.models.chat import Chat
from app.models.character import Character
from app.models.user_persona import UserPersona
from app.models.scenario import Scenario
from app.models.message import Message
from app.models.chat_checkpoint import ChatCheckpoint
from app.schemas.chat import ChatCreate, Chat as ChatSchema
from app.schemas.message import MessageCreate, Message as MessageSchema

router = APIRouter()

# ─── Создание чата (сессии) ──────────────────────────────────────────────── #

@router.post("/", response_model=ChatSchema, status_code=status.HTTP_201_CREATED)
async def create_chat(
    chat_in: ChatCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Создать новый чат с AI-персонажем."""
    character = await db.get(Character, chat_in.character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    persona = await db.get(UserPersona, chat_in.user_persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    if str(persona.owner_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="You can only use your own personas")

    scenario = None
    if chat_in.scenario_id:
        scenario = await db.get(Scenario, chat_in.scenario_id)
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")

    chat = Chat(
        user_id=current_user.id,
        character_id=character.id,
        user_persona_id=persona.id,
        scenario_id=scenario.id if scenario else None,
        mode="scenario" if scenario else "sandbox",
        is_acquainted=chat_in.is_acquainted,
        relationship_dynamic=chat_in.relationship_dynamic,
        language=chat_in.language,
        narrative_voice=chat_in.narrative_voice,
    )

    db.add(chat)
    
    # Инкремент общего счетчика чатов персонажа
    character.total_chats_count += 1
    
    await db.commit()
    await db.refresh(chat)
    
    
    # [Блок 10] Инициализация сценария (Генерация маршрута)
    if chat.mode == "scenario":
        from app.core.director_service import DirectorService
        director = DirectorService()
        
        # Ограничиваем кол-во точек от 2 до 6
        cp_count = max(2, min(6, chat_in.checkpoints_count))
        
        # В фоне, чтобы не тормозить создание чата
        background_tasks.add_task(director.initialize_scenario, chat.id, cp_count)

    return chat


# ─── Список чатов пользователя ───────────────────────────────────────────── #

@router.get("/", response_model=List[ChatSchema])
async def list_chats(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    query = (
        select(Chat)
        .where(Chat.user_id == current_user.id)
        .order_by(Chat.updated_at.desc().nulls_last())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


# ─── Получить чат по ID ───────────────────────────────────────────────────── #

@router.get("/{chat_id}", response_model=ChatSchema)
async def get_chat(
    chat_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    chat = await db.get(Chat, chat_id)
    if not chat or str(chat.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


# ─── Удалить чат ─────────────────────────────────────────────────────────── #

@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    chat = await db.get(Chat, chat_id)
    if not chat or str(chat.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Chat not found")
    await db.delete(chat)
    await db.commit()


# ─── Отправить сообщение (основной endpoint) ─────────────────────────────── #

@router.post("/{chat_id}/messages/stream")
async def send_message_stream(
    chat_id: UUID,
    message_in: MessageCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """
    Отправить сообщение и получить ответ AI SSE.
    """
    chat = await db.get(Chat, chat_id)
    if not chat or str(chat.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Chat not found")

    character = await db.get(Character, chat.character_id)
    persona = await db.get(UserPersona, chat.user_persona_id)
    scenario = await db.get(Scenario, chat.scenario_id) if chat.scenario_id else None

    # Сохраняем сообщение пользователя
    user_msg = Message(
        chat_id=chat.id,
        role="user",
        content=message_in.content,
        parent_id=message_in.parent_id,
    )
    db.add(user_msg)
    await db.commit()
    await db.refresh(user_msg)
    print(f"[DEBUG] user_msg saved: id={user_msg.id}, parent_id={user_msg.parent_id}")

    # ─── Сборка промпта через конвейер ─────────────────────────────────────── #
    from app.core.prompt_pipeline import PromptPipeline
    pipeline = PromptPipeline(db, chat_id, current_user=current_user, parent_id=message_in.parent_id)
    payload = await pipeline.build_payload(message_in.content)
    
    # [Блок 10] Обновление счетчика текущего чекпоинта происходит в stream_utils.process_post_generation
    
    # Создаем "пустое" сообщение ИИ
    ai_msg = Message(
        chat_id=chat.id,
        role="assistant",
        content="",
        parent_id=user_msg.id,
    )
    db.add(ai_msg)
    
    # Обновляем active_leaf_id чата напрямую через атрибут колонки (минуя relationship)
    await db.flush()  # Получаем id для ai_msg до commit
    await db.execute(
        sa_update(Chat)
        .where(Chat.id == chat.id)
        .values(active_leaf_id=ai_msg.id)
    )
    await db.commit()
    await db.refresh(ai_msg)
    print(f"[DEBUG] ai_msg saved: id={ai_msg.id}, parent_id={ai_msg.parent_id}")

    # Перечитываем chat чтобы убедиться что active_leaf_id сохранён
    await db.refresh(chat)
    print(f"[DEBUG] chat.active_leaf_id after commit={chat.active_leaf_id}")

    # ─── Стрим ответа ──────────────────────────────────────────────────────── #
    from app.api.endpoints.stream_utils import generate_chat_stream, process_post_generation
    from fastapi.responses import StreamingResponse
    
    state = {}
    generator = generate_chat_stream(chat.id, ai_msg.id, payload, state)

    return StreamingResponse(generator, media_type="text/event-stream")


# ─── Вспомогательная функция построения узла дерева ─────────────────────── #

def _build_msg_node(msg, children_map: dict) -> dict:
    brothers = children_map.get(msg.parent_id, [])
    try:
        current_index = brothers.index(msg) + 1
    except ValueError:
        current_index = 1
    return {
        "id": msg.id,
        "role": msg.role,
        "content": msg.content,
        "hidden_thought": msg.hidden_thought if msg.role == "assistant" else None,
        "is_edited": msg.is_edited,
        "parent_id": msg.parent_id,
        "created_at": msg.created_at,
        "siblings_count": len(brothers),
        "current_sibling_index": current_index,
        # Ids прямых детей — фронт может строить дерево без доп. запросов
        "children_ids": [c.id for c in children_map.get(msg.id, [])],
    }


# ─── Получить историю сообщений ──────────────────────────────────────────── #

@router.get("/{chat_id}/history")
async def get_chat_history(
    chat_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """
    Возвращает:
    - active_leaf_id: ID текущего активного листа.
    - active_branch: линейный список сообщений активной ветки (корень -> лист)
      с siblings_count / current_sibling_index для свайп-UI.
    - tree: плоский список ВСЕХ сообщений чата с теми же метаданными
      (siblings, children_ids) — для построения дерева истории на фронте.

    Один запрос — вся информация. Не нужны дополнительные вызовы API.
    """
    from collections import defaultdict

    chat = await db.get(Chat, chat_id)
    if not chat or str(chat.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Chat not found")

    # ── Чекпоинты (для сценария) ────────────────────────────────────────────── #
    cp_res = await db.execute(
        select(ChatCheckpoint)
        .where(ChatCheckpoint.chat_id == chat_id)
        .order_by(ChatCheckpoint.order_num)
    )
    checkpoints_list = [
        {
            "id": cp.id,
            "order_num": cp.order_num,
            "goal_description": cp.goal_description,
            "is_completed": cp.is_completed
        } for cp in cp_res.scalars().all()
    ]

    # Грузим все сообщения одним запросом
    res = await db.execute(
        select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at)
    )
    all_msgs = res.scalars().all()

    if not all_msgs:
        return {
            "active_leaf_id": None, 
            "active_branch": [], 
            "tree": [],
            "checkpoints": checkpoints_list
        }

    # Строим карту parent_id -> [дети] для расчёта братьев и детей
    children_map: dict = defaultdict(list)
    msg_dict: dict = {}
    for m in all_msgs:
        children_map[m.parent_id].append(m)
        msg_dict[m.id] = m

    for siblings in children_map.values():
        siblings.sort(key=lambda x: x.created_at)

    # ── Полное дерево (flat) ────────────────────────────────────────────────── #
    tree = [_build_msg_node(m, children_map) for m in all_msgs]

    # ── Активная ветка ──────────────────────────────────────────────────────── #
    # Если active_leaf_id не задан или устарел — авто-определяем последний лист
    leaf_id = chat.active_leaf_id
    if not leaf_id or leaf_id not in msg_dict:
        leaves = [m for m in all_msgs if not children_map.get(m.id)]
        leaf_id = leaves[-1].id if leaves else all_msgs[-1].id

    branch = []
    current_id = leaf_id
    while current_id:
        msg = msg_dict.get(current_id)
        if not msg:
            break
        branch.append(_build_msg_node(msg, children_map))
        current_id = msg.parent_id

    branch.reverse()

    return {
        "active_leaf_id": leaf_id,
        "active_branch": branch,
        "tree": tree,
        "checkpoints": checkpoints_list
    }

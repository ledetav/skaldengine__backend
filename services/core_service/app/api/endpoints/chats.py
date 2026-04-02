from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api import deps
from app.core.config import settings
from google import genai
from google.genai import types
from app.models.chat import Chat
from app.models.character import Character
from app.models.user_persona import UserPersona
from app.models.scenario import Scenario
from app.models.message import Message
from app.schemas.chat import ChatCreate, Chat as ChatSchema
from app.schemas.message import MessageCreate, Message as MessageSchema

router = APIRouter()

# Gemini client (одиночный экземпляр на всё приложение)
_client = genai.Client(api_key=settings.GEMINI_API_KEY)


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
    await db.commit()
    await db.refresh(chat)
    
    
    # [Блок 10] Инициализация сценария (Генерация маршрута)
    if chat.mode == "scenario":
        from app.core.director_service import DirectorService
        director = DirectorService()
        # В фоне, чтобы не тормозить создание чата
        background_tasks.add_task(director.initialize_scenario, chat.id)

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

@router.post("/{chat_id}/messages", response_model=MessageSchema)
async def send_message(
    chat_id: UUID,
    message_in: MessageCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """
    Отправить сообщение и получить ответ AI.
    Поддерживает parent_id для ветвления (swipe).
    TODO: заменить на SSE-стриминг в следующих блоках.
    """
    chat = await db.get(Chat, chat_id)
    if not chat or str(chat.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Chat not found")

    # Загружаем связанные объекты для системного промпта
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


    # ─── Сборка промпта через конвейер (Block 7) ─────────────────────────── #
    from app.core.prompt_pipeline import PromptPipeline
    pipeline = PromptPipeline(db, chat_id, parent_id=message_in.parent_id)
    payload = await pipeline.build_payload(message_in.content)
    
    # [Блок 10] Обновление счетчика текущего чекпоинта
    # Мы берем текущую невыполненную задачу и инкрементируем счетчик
    from app.models.chat_checkpoint import ChatCheckpoint
    res = await db.execute(
        select(ChatCheckpoint)
        .where(ChatCheckpoint.chat_id == chat_id, ChatCheckpoint.is_completed == False)
        .order_by(ChatCheckpoint.order_num)
    )
    checkpoint = res.scalars().first()
    if checkpoint:
        checkpoint.messages_spent += 1
        db.add(checkpoint)
        await db.commit()

        # Фоновый мониторинг (Watcher Loop) - запускаем раз в 3 сообщения
        if checkpoint.messages_spent % 3 == 0:
            from app.core.director_service import DirectorService
            director = DirectorService()
            background_tasks.add_task(director.check_progress, chat_id)
    
    # Вызов Gemini
    ai_text = ""
    hidden_thought = ""
    try:
        # Используем параметры из пайплайна
        response = _client.models.generate_content(
            model="gemini-2.0-flash",
            contents=payload["contents"],
            config=payload["config"]
        )
        full_text = response.text or ""
        
        # Парсим <Internal_Analysis> если он есть
        import re
        thought_match = re.search(r"<Internal_Analysis>(.*?)</Internal_Analysis>", full_text, re.DOTALL)
        if thought_match:
            hidden_thought = thought_match.group(1).strip()
            ai_text = re.sub(r"<Internal_Analysis>.*?</Internal_Analysis>", "", full_text, flags=re.DOTALL).strip()
        else:
            ai_text = full_text.strip()
            
    except Exception as e:
        print(f"[Gemini] Error: {e}")
        ai_text = "(System Error: Neural network unavailable)"

    # Сохраняем ответ AI
    ai_msg = Message(
        chat_id=chat.id,
        role="assistant",
        content=ai_text,
        hidden_thought=hidden_thought,
        parent_id=user_msg.id,
    )
    db.add(ai_msg)

    # Обновляем active_leaf_id чата
    chat.active_leaf_id = ai_msg.id
    db.add(chat)

    await db.commit()
    await db.refresh(ai_msg)

    return ai_msg


# ─── Получить историю сообщений ──────────────────────────────────────────── #

@router.get("/{chat_id}/messages", response_model=List[MessageSchema])
async def get_messages(
    chat_id: UUID,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    chat = await db.get(Chat, chat_id)
    if not chat or str(chat.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Chat not found")

    query = (
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.asc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()

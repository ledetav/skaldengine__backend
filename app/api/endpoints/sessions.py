from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.api import deps
from app.core import prompt_builder, rag  # Импортируем наши модули
from google.genai import types
from app.models.user import User
from app.models.session import Session
from app.models.character import Character
from app.models.user_persona import UserPersona
from app.models.scenario import Scenario
from app.models.message import Message
from app.schemas.session import SessionCreate, Session as SessionSchema
from app.schemas.message import MessageCreate, Message as MessageSchema

router = APIRouter()

@router.post("/", response_model=SessionSchema, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_in: SessionCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Начать новую игру.
    1. Проверяет существование персонажа и персоны.
    2. Генерирует системный промпт (Prompt Builder).
    3. Создает сессию со "снэпшотами" имен.
    """
    
    # 1. Загружаем и проверяем сущности
    character = await db.get(Character, session_in.character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    persona = await db.get(UserPersona, session_in.persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
        
    # Важно: нельзя играть чужой персоной
    if str(persona.owner_id) != str(current_user.id):
         raise HTTPException(status_code=403, detail="You can only use your own personas")

    scenario = None
    if session_in.scenario_id:
        scenario = await db.get(Scenario, session_in.scenario_id)
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")

    system_prompt = prompt_builder.build_system_prompt(
        character=character,
        persona=persona,
        scenario=scenario,
        speech_style=session_in.speech_style,
        language=session_in.language,
        relationship_context=session_in.relationship_context
    )

    new_session = Session(
        user_id=str(current_user.id),
        character_id=str(character.id),
        persona_id=str(persona.id),
        scenario_id=str(scenario.id) if scenario else None,
        
        mode="scenario" if scenario else "sandbox",
        language=session_in.language,
        speech_style=session_in.speech_style,
        
        # Снэпшоты (Замораживаем имена на момент начала игры)
        character_name_snapshot=character.name,
        persona_name_snapshot=persona.name,
        
        # Кэш промпта (храним, чтобы не пересобирать каждый раз)
        cached_system_prompt=system_prompt
    )
    
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    
    return new_session

@router.get("/", response_model=List[SessionSchema])
async def read_my_sessions(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Получить историю моих игр (от новых к старым)"""
    query = select(Session)\
        .where(Session.user_id == current_user.id)\
        .order_by(Session.updated_at.desc())\
        .offset(skip)\
        .limit(limit)
        
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{session_id}", response_model=SessionSchema)
async def read_session(
    session_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Получить одну сессию по ID (чтобы открыть чат)"""
    session = await db.get(Session, str(session_id))
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if str(session.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not your session")
        
    return session

@router.post("/{session_id}/chat", response_model=MessageSchema)
async def send_message(
    session_id: UUID,
    message_in: MessageCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Отправить сообщение боту.
    Логика: User Msg -> DB -> RAG Search -> Load History -> Gemini -> AI Msg -> DB.
    """
    # Проверяем сессию и права
    session = await db.get(Session, str(session_id))
    if not session or str(session.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Session not found")

    # Сохраняем сообщение пользователя
    user_msg = Message(
        session_id=str(session.id),
        role="user",
        content=message_in.content
    )
    db.add(user_msg)
    await db.commit() # Получаем ID и timestamp
    
    # RAG: Ищем факты (Lore) в ChromaDB
    # Ищем факты о персонаже, похожие на сообщение пользователя
    relevant_lore = rag.search_relevant_lore(
        query=message_in.content, 
        character_id=str(session.character_id),
        k=3
    )
    
    # Если нашли факты, форматируем их в блок текста
    lore_injection = ""
    if relevant_lore:
        lore_injection = "\n[RECALLED MEMORY / FACTS]\n" + "\n".join(relevant_lore)

    # Загружаем историю чата (Последние 20 сообщений)
    history_query = select(Message)\
        .where(Message.session_id == session.id)\
        .order_by(Message.created_at.desc())\
        .limit(20)
        
    history_result = await db.execute(history_query)
    # Разворачиваем (DB отдает от новых к старым, нам надо от старых к новым)
    db_messages = history_result.scalars().all()[::-1] 
    
    # Формируем список для Gemini SDK
    gemini_history = []
    for msg in db_messages:
        if msg.id == user_msg.id:
            continue
            
        role = "user" if msg.role == "user" else "model"
        gemini_history.append(types.Content(role=role, parts=[types.Part(text=msg.content)]))
        
    # Добавляем текущее сообщение в конец истории
    gemini_history.append(types.Content(role="user", parts=[types.Part(text=message_in.content)]))

    # 5. Склеиваем финальный системный промпт
    # Базовый промпт (из сессии) + RAG факты (динамически)
    full_system_instruction = session.cached_system_prompt + lore_injection

    # 6. Отправляем в Gemini
    ai_text = ""
    try:
        response = rag.client.models.generate_content(
            model="gemini-3-flash-preview", # Используем быструю и умную модель
            contents=gemini_history,
            config={
                "system_instruction": full_system_instruction,
                "temperature": 1.15, # Чуть выше для креативности
                "max_output_tokens": 30000,
            }
        )
        ai_text = response.text
    except Exception as e:
        print(f"Gemini API Error: {e}")
        ai_text = "(System Error: The neural network is currently unavailable. Please try again.)"

    # 7. Сохраняем ответ ИИ
    ai_msg = Message(
        session_id=str(session.id),
        role="assistant",
        content=ai_text
    )
    db.add(ai_msg)
    
    # Обновляем timestamp сессии
    session.updated_at = ai_msg.created_at # или datetime.utcnow()
    db.add(session)
    
    await db.commit()
    await db.refresh(ai_msg)
    
    return ai_msg

@router.get("/{session_id}/messages", response_model=List[MessageSchema])
async def read_messages(
    session_id: UUID,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Получить историю сообщений для фронтенда"""
    session = await db.get(Session, session_id)
    if not session or str(session.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Session not found")
        
    query = select(Message)\
        .where(Message.session_id == session_id)\
        .order_by(Message.created_at.asc())\
        .offset(skip)\
        .limit(limit)
        
    result = await db.execute(query)
    return result.scalars().all()
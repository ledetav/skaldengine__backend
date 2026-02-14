from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.api import deps
from app.core import prompt_builder, rag
from app.core.kafka import send_entity_event
from google.genai import types
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
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    character = await db.get(Character, session_in.character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    persona = await db.get(UserPersona, session_in.persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
        
    # Проверка владельца (owner_id теперь UUID)
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
        user_id=current_user.id,
        character_id=character.id,
        persona_id=persona.id,
        scenario_id=scenario.id if scenario else None,
        
        mode="scenario" if scenario else "sandbox",
        language=session_in.language,
        speech_style=session_in.speech_style,
        
        character_name_snapshot=character.name,
        persona_name_snapshot=persona.name,
        cached_system_prompt=system_prompt
    )
    
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    
    await send_entity_event(
        event_type="Created",
        entity_type="Session",
        entity_id=str(new_session.id),
        payload={"character_name": character.name, "persona_name": persona.name}
    )
    
    return new_session

@router.get("/", response_model=List[SessionSchema])
async def read_my_sessions(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    query = select(Session)\
        .where(Session.user_id == current_user.id)\
        .order_by(Session.updated_at.desc().nulls_last())\
        .offset(skip)\
        .limit(limit)
        
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{session_id}", response_model=SessionSchema)
async def read_session(
    session_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    session = await db.get(Session, session_id)
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
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    session = await db.get(Session, session_id)
    if not session or str(session.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Session not found")

    user_msg = Message(
        session_id=session.id,
        role="user",
        content=message_in.content
    )
    db.add(user_msg)
    await db.commit()
    
    await send_entity_event(
        event_type="Created",
        entity_type="Message",
        entity_id=str(user_msg.id),
        payload={"role": "user", "session_id": str(session.id)}
    ) 
    
    relevant_lore = rag.search_relevant_lore(
        query=message_in.content, 
        character_id=str(session.character_id),
        k=3
    )
    
    lore_injection = ""
    if relevant_lore:
        lore_injection = "\n[RECALLED MEMORY / FACTS]\n" + "\n".join(relevant_lore)

    history_query = select(Message)\
        .where(Message.session_id == session.id)\
        .order_by(Message.created_at.desc())\
        .limit(20)
        
    history_result = await db.execute(history_query)
    db_messages = history_result.scalars().all()[::-1] 
    
    gemini_history = []
    for msg in db_messages:
        if msg.id == user_msg.id:
            continue
            
        role = "user" if msg.role == "user" else "model"
        gemini_history.append(types.Content(role=role, parts=[types.Part(text=msg.content)]))
        
    gemini_history.append(types.Content(role="user", parts=[types.Part(text=message_in.content)]))

    full_system_instruction = session.cached_system_prompt + lore_injection

    ai_text = ""
    try:
        response = rag.client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=gemini_history,
            config={
                "system_instruction": full_system_instruction,
                "temperature": 1.15,
                "max_output_tokens": 8192,
            }
        )
        ai_text = response.text
    except Exception as e:
        print(f"Gemini API Error: {e}")
        ai_text = "(System Error: Neural network unavailable)"

    ai_msg = Message(
        session_id=session.id,
        role="assistant",
        content=ai_text
    )
    db.add(ai_msg)
    session.updated_at = ai_msg.created_at
    db.add(session)
    
    await db.commit()
    await db.refresh(ai_msg)
    
    await send_entity_event(
        event_type="Created",
        entity_type="Message",
        entity_id=str(ai_msg.id),
        payload={"role": "assistant", "session_id": str(session.id)}
    )
    
    return ai_msg

@router.get("/{session_id}/messages", response_model=List[MessageSchema])
async def read_messages(
    session_id: UUID,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
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

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    session = await db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if str(session.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not your session")
    
    await db.delete(session)
    await db.commit()
    
    await send_entity_event(
        event_type="Deleted",
        entity_type="Session",
        entity_id=str(session_id),
        payload={"character_name": session.character_name_snapshot}
    )
    
    return None

@router.put("/{session_id}/messages/{message_id}", response_model=MessageSchema)
async def update_message(
    session_id: UUID,
    message_id: UUID,
    message_in: MessageCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    session = await db.get(Session, session_id)
    if not session or str(session.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    message = await db.get(Message, message_id)
    if not message or str(message.session_id) != str(session_id):
        raise HTTPException(status_code=404, detail="Message not found")
    
    message.content = message_in.content
    db.add(message)
    await db.commit()
    await db.refresh(message)
    
    await send_entity_event(
        event_type="Updated",
        entity_type="Message",
        entity_id=str(message_id),
        payload={"session_id": str(session_id)}
    )
    
    return message

@router.delete("/{session_id}/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    session_id: UUID,
    message_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    session = await db.get(Session, session_id)
    if not session or str(session.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    message = await db.get(Message, message_id)
    if not message or str(message.session_id) != str(session_id):
        raise HTTPException(status_code=404, detail="Message not found")
    
    await db.delete(message)
    await db.commit()
    
    await send_entity_event(
        event_type="Deleted",
        entity_type="Message",
        entity_id=str(message_id),
        payload={"session_id": str(session_id), "role": message.role}
    )
    
    return None

@router.post("/{session_id}/messages/{message_id}/regenerate", response_model=MessageSchema)
async def regenerate_message(
    session_id: UUID,
    message_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    session = await db.get(Session, session_id)
    if not session or str(session.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    original_message = await db.get(Message, message_id)
    if not original_message or str(original_message.session_id) != str(session_id):
        raise HTTPException(status_code=404, detail="Message not found")
    
    if original_message.role != "assistant":
        raise HTTPException(status_code=400, detail="Can only regenerate assistant messages")
    
    original_message.is_active = False
    db.add(original_message)
    
    history_query = select(Message)\
        .where(Message.session_id == session.id, Message.is_active == True)\
        .order_by(Message.created_at.desc())\
        .limit(20)
    history_result = await db.execute(history_query)
    db_messages = history_result.scalars().all()[::-1]
    
    gemini_history = []
    for msg in db_messages:
        if msg.id == message_id:
            break
        role = "user" if msg.role == "user" else "model"
        gemini_history.append(types.Content(role=role, parts=[types.Part(text=msg.content)]))
    
    relevant_lore = rag.search_relevant_lore(
        query=gemini_history[-1].parts[0].text if gemini_history else "",
        character_id=str(session.character_id),
        k=3
    )
    
    lore_injection = ""
    if relevant_lore:
        lore_injection = "\n[RECALLED MEMORY / FACTS]\n" + "\n".join(relevant_lore)
    
    full_system_instruction = session.cached_system_prompt + lore_injection
    
    ai_text = ""
    try:
        response = rag.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=gemini_history,
            config={
                "system_instruction": full_system_instruction,
                "temperature": 1.15,
                "max_output_tokens": 8192,
            }
        )
        ai_text = response.text
    except Exception as e:
        print(f"Gemini API Error: {e}")
        ai_text = "(System Error: Neural network unavailable)"
    
    new_message = Message(
        session_id=session.id,
        parent_id=original_message.parent_id,
        role="assistant",
        content=ai_text,
        is_active=True
    )
    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)
    
    await send_entity_event(
        event_type="Created",
        entity_type="Message",
        entity_id=str(new_message.id),
        payload={"role": "assistant", "session_id": str(session_id), "regenerated": True}
    )
    
    return new_message
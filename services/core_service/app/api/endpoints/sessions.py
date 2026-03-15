import uuid
from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api import deps
from app.core import prompt_builder, rag
from app.core.kafka import publish_domain_event
from app.schemas.events import SessionCreatedEvent, MessageAddedEvent
from google.genai import types
from app.models.character import Character
from app.models.user_persona import UserPersona
from app.models.scenario import Scenario
from app.models.session import Session
from app.models.message import Message

from app.schemas.session import SessionCreate
from app.schemas.message import MessageCreate

router = APIRouter()

async def fetch_branch_messages(session_id: UUID, db: AsyncSession, leaf_parent_id: Optional[UUID]) -> List[Message]:
    if not leaf_parent_id:
        return []
    
    result = await db.execute(select(Message).where(Message.session_id == session_id))
    all_messages = result.scalars().all()
    msg_dict = {msg.id: msg for msg in all_messages}
    branch = []
    
    current_id = leaf_parent_id
    while current_id in msg_dict:
        msg = msg_dict[current_id]
        branch.append(msg)
        current_id = msg.parent_id
        
    return branch[::-1]

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_session(
    session_in: SessionCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    character = await db.get(Character, session_in.character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    persona = await db.get(UserPersona, session_in.persona_id)
    if not persona or persona.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Persona not found or access denied")

    scenario = None
    if session_in.scenario_id:
        scenario = await db.get(Scenario, session_in.scenario_id)
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")

    character_dict = {"name": character.name, "appearance": character.appearance, 
                      "personality_traits": character.personality_traits, "dialogue_style": character.dialogue_style,
                      "inner_world": character.inner_world, "behavioral_cues": character.behavioral_cues}
    persona_dict = {"name": persona.name, "description": persona.description}
    scenario_dict = {"title": scenario.title, "description": scenario.description, 
                     "start_point": scenario.start_point, "end_point": scenario.end_point} if scenario else None

    system_prompt = prompt_builder.build_system_prompt(
        character=character_dict, persona=persona_dict, scenario=scenario_dict,
        speech_style=session_in.speech_style, language=session_in.language,
        relationship_context=session_in.relationship_context
    )

    new_session_id = uuid.uuid4()
    event = SessionCreatedEvent(
        entity_id=new_session_id,
        user_id=current_user.id,
        character_id=character.id,
        persona_id=persona.id,
        scenario_id=scenario.id if scenario else None,
        mode="scenario" if scenario else "sandbox",
        language=session_in.language,
        speech_style=session_in.speech_style,
        character_name_snapshot=character.name,
        persona_name_snapshot=persona.name,
        relationship_context=session_in.relationship_context,
        cached_system_prompt=system_prompt
    )

    await publish_domain_event(event)

    return {"id": new_session_id, "status": "Event published"}

@router.post("/{session_id}/chat")
async def send_message(
    session_id: uuid.UUID,
    message_in: MessageCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    session = await db.get(Session, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found or access denied")

    user_msg_id = uuid.uuid4()
    await publish_domain_event(MessageAddedEvent(
        entity_id=user_msg_id, session_id=session_id,
        parent_id=message_in.parent_id, role="user", content=message_in.content
    ))

    branch_messages = await fetch_branch_messages(session_id, db, message_in.parent_id)
    
    gemini_history = []
    for msg in branch_messages:
        role = "user" if msg.role == "user" else "model"
        gemini_history.append(types.Content(role=role, parts=[types.Part(text=msg.content)]))
    gemini_history.append(types.Content(role="user", parts=[types.Part(text=message_in.content)]))

    relevant_lore = rag.search_relevant_lore(query=message_in.content, character_id=session.character_id, k=3)
    lore_injection = ("\n[RECALLED MEMORY / FACTS]\n" + "\n".join(relevant_lore)) if relevant_lore else ""
    full_system_instruction = session.cached_system_prompt + lore_injection

    try:
        response = rag.client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=gemini_history[-20:],
            config={"system_instruction": full_system_instruction, "temperature": 1.15, "max_output_tokens": 8192}
        )
        ai_text = response.text
    except Exception as e:
        ai_text = "(System Error: Neural network unavailable)"

    ai_msg_id = uuid.uuid4()
    await publish_domain_event(MessageAddedEvent(
        entity_id=ai_msg_id, session_id=session_id,
        parent_id=user_msg_id, role="assistant", content=ai_text
    ))
    
    return {"id": ai_msg_id, "role": "assistant", "content": ai_text}
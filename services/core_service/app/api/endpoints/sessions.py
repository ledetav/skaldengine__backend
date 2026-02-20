import uuid
from uuid import UUID
from typing import List, Optional
import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core import prompt_builder, rag
from app.core.kafka import publish_domain_event
from app.schemas.events import SessionCreatedEvent, MessageAddedEvent
from google.genai import types

from app.schemas.session import SessionCreate
from app.schemas.message import MessageCreate

router = APIRouter()
QUERY_SERVICE_URL = "http://localhost:8002/api/v1"

async def fetch_from_query(endpoint: str, auth_header: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{QUERY_SERVICE_URL}{endpoint}", 
            headers={"Authorization": auth_header}
        )
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Resource not found")
        response.raise_for_status()
        return response.json()

async def fetch_branch_messages_from_query(session_id: str, auth_header: str, leaf_parent_id: Optional[str]) -> List[dict]:
    if not leaf_parent_id:
         return []
         
    all_messages = await fetch_from_query(f"/sessions/{session_id}/messages", auth_header)
    msg_dict = {msg["id"]: msg for msg in all_messages}
    branch = []
    
    current_id = str(leaf_parent_id)
    while current_id in msg_dict:
        msg = msg_dict[current_id]
        branch.append(msg)
        current_id = msg.get("parent_id")
        
    return branch[::-1]

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_session(
    session_in: SessionCreate,
    request: Request,
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    auth_header = request.headers.get("Authorization")
    
    character = await fetch_from_query(f"/characters/{session_in.character_id}", auth_header)
    persona = await fetch_from_query(f"/personas/{session_in.persona_id}", auth_header)
    
    if str(persona["owner_id"]) != str(current_user.id):
        raise HTTPException(status_code=400, detail="Invalid persona")

    scenario = None
    if session_in.scenario_id:
        scenario = await fetch_from_query(f"/scenarios/{session_in.scenario_id}", auth_header)

    system_prompt = prompt_builder.build_system_prompt(
        character=character, persona=persona, scenario=scenario,
        speech_style=session_in.speech_style, language=session_in.language,
        relationship_context=session_in.relationship_context
    )

    new_session_id = uuid.uuid4()
    event = SessionCreatedEvent(
        entity_id=new_session_id,
        user_id=current_user.id,
        character_id=UUID(character["id"]),
        persona_id=UUID(persona["id"]),
        scenario_id=UUID(scenario["id"]) if scenario else None,
        mode="scenario" if scenario else "sandbox",
        language=session_in.language,
        speech_style=session_in.speech_style,
        character_name_snapshot=character["name"],
        persona_name_snapshot=persona["name"],
        relationship_context=session_in.relationship_context,
        cached_system_prompt=system_prompt
    )

    await publish_domain_event(event)

    return {"id": new_session_id, "status": "Event published"}

@router.post("/{session_id}/chat")
async def send_message(
    session_id: uuid.UUID,
    message_in: MessageCreate,
    request: Request,
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    auth_header = request.headers.get("Authorization")
    session_data = await fetch_from_query(f"/sessions/{session_id}", auth_header)

    user_msg_id = uuid.uuid4()
    await publish_domain_event(MessageAddedEvent(
        entity_id=user_msg_id, session_id=session_id,
        parent_id=message_in.parent_id, role="user", content=message_in.content
    ))

    branch_messages = await fetch_branch_messages_from_query(str(session_id), auth_header, message_in.parent_id)
    
    gemini_history = []
    for msg in branch_messages:
        role = "user" if msg["role"] == "user" else "model"
        gemini_history.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))
    gemini_history.append(types.Content(role="user", parts=[types.Part(text=message_in.content)]))

    relevant_lore = rag.search_relevant_lore(query=message_in.content, character_id=session_data["character_id"], k=3)
    lore_injection = ("\n[RECALLED MEMORY / FACTS]\n" + "\n".join(relevant_lore)) if relevant_lore else ""
    full_system_instruction = session_data["cached_system_prompt"] + lore_injection

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
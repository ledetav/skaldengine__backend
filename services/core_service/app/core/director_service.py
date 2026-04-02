import json
import re
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from google import genai
from google.genai import types

from app.core.config import settings
from app.db.base import AsyncSessionLocal
from app.models.chat import Chat
from app.models.character import Character
from app.models.user_persona import UserPersona
from app.models.scenario import Scenario
from app.models.message import Message
from app.models.chat_checkpoint import ChatCheckpoint

class DirectorService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    async def initialize_scenario(self, chat_id: uuid.UUID):
        """Фаза 1: Генерация маршрута (чекпоинтов) при создании чата."""
        async with AsyncSessionLocal() as db:
            # 1. Получаем данные чата
            result = await db.execute(
                select(Chat, Character, UserPersona, Scenario)
                .join(Character, Chat.character_id == Character.id)
                .join(UserPersona, Chat.user_persona_id == UserPersona.id)
                .join(Scenario, Chat.scenario_id == Scenario.id)
                .where(Chat.id == chat_id)
            )
            row = result.first()
            if not row:
                return

            chat, character, persona, scenario = row

            # 2. Form prompt for scenario generation
            prompt = f"""You are a Professional RPG Scenario Writer.
Your task is to plot a logical narrative path from Point A (Inciting Incident) to Point B (Finale) for two characters.

[AI CHARACTER]: {character.name} - {character.description or 'No description'}
[USER CHARACTER]: {persona.name} - {persona.description or 'No description'}
[RELATIONSHIP DYNAMIC]: {chat.relationship_dynamic or 'Initial meeting'}

[POINT A (Start)]: {scenario.start_point}
[POINT B (End)]: {scenario.end_point}

Create between 2 to 6 intermediate narrative goals (checkpoints) that must be fulfilled in order to logically progress from Point A to Point B.
Each goal must be formulated as a hidden directive for the AI actor (what they should push the player to do, or what event must occur).

Return a JSON array of objects with the "goal_description" field. All goals must be written in {chat.language or 'Russian'}."""

            try:
                # Используем Flash для скорости и JSON mode
                response = await self.client.aio.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.7
                    )
                )
                
                checkpoints_data = json.loads(response.text)
                if isinstance(checkpoints_data, dict) and "checkpoints" in checkpoints_data:
                    checkpoints_list = checkpoints_data["checkpoints"]
                elif isinstance(checkpoints_data, list):
                    checkpoints_list = checkpoints_data
                else:
                    checkpoints_list = []

                # 3. Сохраняем в БД
                for i, cp_data in enumerate(checkpoints_list):
                    goal = cp_data.get("goal_description")
                    if goal:
                        checkpoint = ChatCheckpoint(
                            chat_id=chat_id,
                            order_num=i + 1,
                            goal_description=goal,
                            is_completed=False,
                            messages_spent=0
                        )
                        db.add(checkpoint)
                
                await db.commit()
                print(f"[Director] Generated {len(checkpoints_list)} checkpoints for chat {chat_id}")

            except Exception as e:
                print(f"[Director] Error initializing scenario: {e}")
                await db.rollback()

    async def check_progress(self, chat_id: uuid.UUID):
        """Фаза 2: Фоновый мониторинг (The Watcher Loop)."""
        async with AsyncSessionLocal() as db:
            # 1. Берем текущую активную цель
            result = await db.execute(
                select(ChatCheckpoint)
                .where(ChatCheckpoint.chat_id == chat_id, ChatCheckpoint.is_completed == False)
                .order_by(ChatCheckpoint.order_num)
            )
            current_checkpoint = result.scalars().first()
            if not current_checkpoint:
                return # Сценарий завершен или целей нет

            # 2. Берем последние 8 сообщений для контекста
            msg_result = await db.execute(
                select(Message)
                .where(Message.chat_id == chat_id)
                .order_by(desc(Message.created_at))
                .limit(8)
            )
            messages = list(reversed(msg_result.scalars().all()))
            history_text = "\n".join([f"{m.role}: {m.content}" for m in messages])

            # 3. Request to Supervisor
            prompt = f"""You are a Narrative Supervisor. Your task is to objectively evaluate the progress of a roleplaying scene.

[CURRENT SCENARIO GOAL]: "{current_checkpoint.goal_description}"

[RECENT MESSAGES]:
{history_text}

Analyze the dialogue. Has the current narrative goal been effectively achieved or fully disclosed? 
Note: A goal is considered achieved ONLY if the event has already occurred or the fact is already clearly established in the dialogue, not just mentioned as future plans.

Return JSON:
{{
  "reasoning": "Brief logical explanation of your decision (up to 30 words).",
  "is_achieved": true/false
}}"""

            try:
                response = await self.client.aio.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.1
                    )
                )
                
                analysis = json.loads(response.text)
                if analysis.get("is_achieved"):
                    # 4. Мутация состояния
                    current_checkpoint.is_completed = True
                    db.add(current_checkpoint)
                    await db.commit()
                    print(f"[Director] Checkpoint {current_checkpoint.order_num} achieved for chat {chat_id}: {analysis.get('reasoning')}")
                else:
                    print(f"[Director] Progress check for chat {chat_id}: Not achieved yet. Reason: {analysis.get('reasoning')}")

            except Exception as e:
                print(f"[Director] Error checking progress: {e}")

import json
import uuid
from sqlalchemy import select, desc
from openai import AsyncOpenAI

from app.core.config import settings
from app.db.base import AsyncSessionLocal
from app.domains.chat.models import Chat
from app.domains.character.models import Character
from app.domains.persona.models import UserPersona
from app.domains.scenario.models import Scenario
from app.domains.chat.message_models import Message
from app.domains.chat.models import ChatCheckpoint

class DirectorService:
    def __init__(self):
        self.client = AsyncOpenAI(base_url="https://polza.ai/api/v1", api_key=settings.POLZA_API_KEY)

    async def initialize_scenario(self, chat_id: uuid.UUID, checkpoints_count: int = 3):
        """Фаза 1: Генерация маршрута (чекпоинтов) при создании чата."""
        import random
        from sqlalchemy import func, or_
        from app.domains.lorebook.models import Lorebook, LorebookEntry, LorebookType
        from app.domains.character.models import character_lorebook_association

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

            # --- Lorebook Enrichment ---
            lore_facts = []
            
            # 2. Get Potential Lorebooks for Fandom & Character
            # Filters: 
            # - type=FANDOM and fandom matching character.fandom
            # - type=CHARACTER and character_id matching character.id
            # - associated via character_lorebook_association
            
            fandom_q = select(Lorebook).where(
                Lorebook.type == LorebookType.FANDOM,
                Lorebook.fandom == character.fandom
            )
            char_direct_q = select(Lorebook).where(
                Lorebook.type == LorebookType.CHARACTER,
                Lorebook.character_id == character.id
            )
            assoc_q = select(Lorebook).join(
                character_lorebook_association, 
                Lorebook.id == character_lorebook_association.c.lorebook_id
            ).where(character_lorebook_association.c.character_id == character.id)
            
            # Combine potential lorebooks
            l_res_f = await db.execute(fandom_q)
            l_res_c = await db.execute(char_direct_q)
            l_res_a = await db.execute(assoc_q)
            
            potential_books = list(set(
                list(l_res_f.scalars().all()) + 
                list(l_res_c.scalars().all()) + 
                list(l_res_a.scalars().all())
            ))
            
            # Select up to 3 random books
            if len(potential_books) > 3:
                selected_books = random.sample(potential_books, 3)
            else:
                selected_books = potential_books
                
            # Fetch up to 6 random entries from these books
            if selected_books:
                book_ids = [b.id for b in selected_books]
                entries_q = select(LorebookEntry).where(
                    LorebookEntry.lorebook_id.in_(book_ids)
                ).order_by(func.random()).limit(6)
                e_res = await db.execute(entries_q)
                lore_facts.extend([e.content for e in e_res.scalars().all()])

            # 3. Persona Enrichment (if acquainted)
            persona_facts = []
            if chat.is_acquainted:
                pers_books_q = select(Lorebook).where(
                    Lorebook.type == LorebookType.PERSONA,
                    Lorebook.user_persona_id == persona.id
                )
                p_res = await db.execute(pers_books_q)
                p_books = p_res.scalars().all()
                if p_books:
                    p_book = random.choice(p_books)
                    p_entries_q = select(LorebookEntry).where(
                        LorebookEntry.lorebook_id == p_book.id
                    ).order_by(func.random()).limit(3)
                    pe_res = await db.execute(p_entries_q)
                    persona_facts.extend([e.content for e in pe_res.scalars().all()])

            # --- Build Prompt ---
            lore_section = "\n".join([f"- {f}" for f in lore_facts]) if lore_facts else "No specific world lore provided."
            persona_lore_section = "\n".join([f"- {f}" for f in persona_facts]) if persona_facts else ""
            
            relationship_info = f"[RELATIONSHIP]: {chat.relationship_dynamic}" if chat.relationship_dynamic else ""
            if chat.is_acquainted:
                relationship_info = f"[RELATIONSHIP STATUS]: Characters are already acquainted.\n{relationship_info}"
            else:
                relationship_info = "[RELATIONSHIP STATUS]: First meeting."

            scenario_context = scenario.internal_description or scenario.description or "No general description"

            prompt = f"""You are a Professional RPG Scenario Writer.
Your task is to plot a logical narrative path from Point A (Inciting Incident) to Point B (Finale).

[SCENARIO DESCRIPTION]:
{scenario_context}

[AI CHARACTER]: {character.name}
- Personality: {character.personality or 'Internal role instructions'}
- Appearance: {character.appearance or 'Varies'}
- Context/Bio: {character.description or 'No description'}

[USER CHARACTER]: {persona.name}
- Personality: {persona.personality or 'Varies'}
- Appearance: {persona.appearance or 'Varies'}
- Facts/Bio: {persona.facts or 'No facts provided'}
{persona_lore_section}

{relationship_info}

[POINT A (Start)]: {scenario.start_point}
[POINT B (End)]: {scenario.end_point}

[WORLD/CHARACTER LORE FACTS (Randomly selected for uniqueness)]:
{lore_section}

Based on this context, create EXACTLY {checkpoints_count} intermediate narrative goals (checkpoints) that must be fulfilled in order to logically progress from Point A to Point B.
Each goal must be formulated as a hidden directive for the AI actor (what they should push the player to do, or what event must occur).

Return a JSON object with a "checkpoints" key containing an array of objects with the "goal_description" field. All goals must be written strictly in English, regardless of the characters' primary language. Each goal should be a concise narrative milestone. 
Example: "Character A admits their secret to Character B." or "The group reaches the abandoned temple."
"""

            try:
                # Используем Flash для скорости и JSON mode
                response = await self.client.chat.completions.create(
                    model=settings.POLZA_CHAT_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.8
                )
                
                response_text = response.choices[0].message.content
                checkpoints_data = json.loads(response_text)
                if isinstance(checkpoints_data, dict) and "checkpoints" in checkpoints_data:
                    checkpoints_list = checkpoints_data["checkpoints"]
                elif isinstance(checkpoints_data, list):
                    checkpoints_list = checkpoints_data
                else:
                    checkpoints_list = []

                # 3. Сохраняем в БД
                for i, cp_data in enumerate(checkpoints_list[:checkpoints_count]):
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
                response = await self.client.chat.completions.create(
                    model=settings.POLZA_CHAT_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                
                response_text = response.choices[0].message.content
                analysis = json.loads(response_text)
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

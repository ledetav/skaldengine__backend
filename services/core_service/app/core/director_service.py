"""Сервис режиссёра сценария (Director Service) для динамического контроля сюжета."""

from typing import Optional
import json
import uuid
from openai import AsyncOpenAI
from sqlalchemy import select
from app.core.config import settings
from app.db.base import AsyncSessionLocal
from app.domains.chat.models import Chat
from app.domains.character.models import Character
from app.domains.persona.models import UserPersona
from app.domains.scenario.models import Scenario
from app.domains.chat.message_models import Message
from app.domains.chat.models import ChatCheckpoint


class DirectorService:
    """Сервис-режиссёр для генерации контрольных точек сценария и отслеживания их прохождения."""

    def __init__(self):
        """Инициализация клиента OpenAI/Polza.ai."""
        self.client = AsyncOpenAI(base_url="https://polza.ai/api/v1", api_key=settings.POLZA_API_KEY)

    async def initialize_scenario(self, chat_id: uuid.UUID, checkpoints_count: int = 3):
        """Фаза 1: Генерация маршрута сюжета (чекпоинтов) при создании чата.

        Извлекает контекст персонажа, персоны игрока, лорбуков и сценария, после чего
        через LLM строит логическую последовательность промежуточных нарративных целей.

        Args:
            chat_id: Идентификатор чата.
            checkpoints_count: Количество промежуточных чекпоинтов (по умолчанию 3).
        """
        import random
        from sqlalchemy import func
        from app.domains.lorebook.models import Lorebook, LorebookEntry, LorebookType
        from app.domains.character.models import character_lorebook_association

        async with AsyncSessionLocal() as db:
            # 1. Загружаем базовые сущности диалога
            stmt = (
                select(Chat, Character, UserPersona, Scenario)
                .join(Character, Chat.character_id == Character.id)
                .join(UserPersona, Chat.persona_id == UserPersona.id)
                .outerjoin(Scenario, Chat.scenario_id == Scenario.id)
                .where(Chat.id == chat_id)
            )
            res = await db.execute(stmt)
            row = res.first()
            if not row:
                return

            chat, character, persona, scenario = row

            # --- Обогащение контекста лорбуками ---
            lore_facts = []

            # 2. Поиск подходящих лорбуков фандома и персонажа
            # Критерии:
            # - type=FANDOM и совпадение фандома с character.fandom
            # - type=CHARACTER и совпадение с character.id
            # - ассоциация через таблицу связей character_lorebook_association

            fandom_q = select(Lorebook).where(
                Lorebook.type == LorebookType.FANDOM,
                func.lower(Lorebook.fandom) == func.lower(character.fandom)
            )
            char_direct_q = select(Lorebook).where(
                Lorebook.type == LorebookType.CHARACTER,
                Lorebook.character_id == character.id
            )
            assoc_q = select(Lorebook).join(
                character_lorebook_association,
                Lorebook.id == character_lorebook_association.c.lorebook_id
            ).where(character_lorebook_association.c.character_id == character.id)

            # Объединение потенциальных лорбуков
            l_res_f = await db.execute(fandom_q)
            l_res_c = await db.execute(char_direct_q)
            l_res_a = await db.execute(assoc_q)

            potential_books = list(set(
                list(l_res_f.scalars().all()) +
                list(l_res_c.scalars().all()) +
                list(l_res_a.scalars().all())
            ))

            # Выбираем до 3 случайных книг
            if len(potential_books) > 3:
                selected_books = random.sample(potential_books, 3)
            else:
                selected_books = potential_books

            # Извлекаем до 6 случайных записей из выбранных книг
            if selected_books:
                book_ids = [b.id for b in selected_books]
                entries_q = select(LorebookEntry).where(
                    LorebookEntry.lorebook_id.in_(book_ids)
                ).order_by(func.random()).limit(6)
                e_res = await db.execute(entries_q)
                lore_facts.extend([e.content for e in e_res.scalars().all()])

            # 3. Обогащение лором персоны пользователя (если персонажи уже знакомы)
            persona_facts = []
            if chat.is_acquainted:
                pers_books_q = select(Lorebook).where(
                    Lorebook.type == LorebookType.PERSONA,
                    Lorebook.user_persona_id == persona.id
                )
                pb_res = await db.execute(pers_books_q)
                pers_books = list(pb_res.scalars().all())
                if pers_books:
                    pb_ids = [b.id for b in pers_books]
                    p_entries_q = select(LorebookEntry).where(
                        LorebookEntry.lorebook_id.in_(pb_ids)
                    ).order_by(func.random()).limit(4)
                    pe_res = await db.execute(p_entries_q)
                    persona_facts.extend([e.content for e in pe_res.scalars().all()])

            # --- Формирование промпта для генерации чекпоинтов ---
            lore_section = "\n".join([f"- {f}" for f in lore_facts]) if lore_facts else "No specific world lore provided."
            persona_lore_section = "\n".join([f"- {f}" for f in persona_facts]) if persona_facts else ""

            prompt = f"""You are a Master Narrative Designer for an interactive roleplaying game.
Your task is to generate a sequence of {checkpoints_count} concrete, logical intermediate milestones (checkpoints) that bridge the starting premise to the final objective.

[CHARACTER]:
Name: {character.name}
Fandom: {character.fandom}
Personality/Bio: {character.personality or character.description or 'Not specified'}

[PLAYER PERSONA]:
Name: {persona.name}
Description: {persona.description or 'Not specified'}
{f'[PLAYER LORE]:\n{persona_lore_section}' if persona_lore_section else ''}

[WORLD LORE]:
{lore_section}

[SCENARIO]:
Title: {scenario.title if scenario else 'Custom'}
Starting Premise: {scenario.description if scenario else 'Freeform'}
FINAL OBJECTIVE: {scenario.final_goal if scenario and scenario.final_goal else 'Reach a meaningful narrative climax'}

Generate a JSON object with a single key "checkpoints", which is a list of {checkpoints_count} objects.
Each object must have:
- "goal_description": A clear, actionable, third-person narrative milestone that moves the plot closer to the FINAL OBJECTIVE, organically integrating the character's personality and world lore.

Return ONLY valid JSON.
"""

            try:
                # Используем Polza chat model и JSON-режим для надежного парсинга
                response = await self.client.chat.completions.create(
                    model=settings.POLZA_CHAT_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.7
                )
                content = response.choices[0].message.content
                data = json.loads(content)

                if isinstance(data, dict):
                    checkpoints_list = data.get("checkpoints", list(data.values())[0] if data else [])
                elif isinstance(data, list):
                    checkpoints_list = data
                else:
                    checkpoints_list = []

                # 4. Сохраняем сгенерированные чекпоинты в БД
                for i, cp_data in enumerate(checkpoints_list[:checkpoints_count]):
                    goal = cp_data.get("goal_description")
                    if goal:
                        cp = ChatCheckpoint(
                            chat_id=chat_id,
                            order_num=i + 1,
                            goal_description=goal,
                            is_completed=False
                        )
                        db.add(cp)

                # Добавляем финальную цель последним чекпоинтом
                if scenario and scenario.final_goal:
                    final_cp = ChatCheckpoint(
                        chat_id=chat_id,
                        order_num=len(checkpoints_list[:checkpoints_count]) + 1,
                        goal_description=scenario.final_goal,
                        is_completed=False
                    )
                    db.add(final_cp)

                await db.commit()
            except Exception as e:
                print(f"[Director] Error generating checkpoints: {e}")

    async def check_progress(
        self,
        chat_id: uuid.UUID,
        leaf_id: Optional[uuid.UUID] = None
    ):
        """Фаза 2: Фоновый мониторинг выполнения текущей цели (The Watcher Loop).

        Анализирует последние сообщения активной ветки диалога с помощью ИИ-супервайзера
        и отмечает текущий чекпоинт как выполненный (is_completed=True), если цель достигнута.

        Args:
            chat_id: Идентификатор чата.
            leaf_id: Идентификатор активного сообщения ветки (необязательно).
        """
        client = self.client

        async with AsyncSessionLocal() as db:
            # 1. Находим первый невыполненный чекпоинт
            result = await db.execute(
                select(ChatCheckpoint)
                .where(ChatCheckpoint.chat_id == chat_id, ChatCheckpoint.is_completed == False)
                .order_by(ChatCheckpoint.order_num)
            )
            current_checkpoint = result.scalars().first()
            if not current_checkpoint:
                return  # Сценарий завершен или целей нет

            # 2. Определение активной ветки сообщений
            target_leaf_id = leaf_id
            if not target_leaf_id:
                chat_obj = await db.get(Chat, chat_id)
                if chat_obj:
                    target_leaf_id = chat_obj.active_leaf_id

            if not target_leaf_id:
                return

            # Восстанавливаем цепочку сообщений текущей ветки до корня
            branch_msgs = []
            curr_id = target_leaf_id
            visited = set()
            while curr_id and curr_id not in visited and len(branch_msgs) < 50:
                visited.add(curr_id)
                msg_obj = await db.get(Message, curr_id)
                if not msg_obj:
                    break
                branch_msgs.append(msg_obj)
                curr_id = msg_obj.parent_id

            branch_msgs.reverse()

            # Собираем контекст из последних 12 сообщений ветки
            recent_msgs = branch_msgs[-12:]
            history_text = "\n".join([f"{m.role.upper()}: {m.content}" for m in recent_msgs])
            if not history_text:
                return

            # 3. Запрос к нарративному супервайзеру
            prompt = f"""You are a Narrative Supervisor. Your task is to objectively evaluate the progress of a roleplaying scene.

[CURRENT SCENARIO GOAL]: "{current_checkpoint.goal_description}"

[RECENT CHAT HISTORY]:
{history_text}

Has the character/player successfully achieved or clearly completed the [CURRENT SCENARIO GOAL] in the dialogue above?
Evaluate strictly based on explicit actions and dialogue outcomes, not mere intentions.

Return a JSON object: {{"is_achieved": true/false, "reason": "brief explanation"}}
"""
            try:
                response = await client.chat.completions.create(
                    model=settings.POLZA_SUMMARY_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                response_text = response.choices[0].message.content
                analysis = json.loads(response_text)
                if analysis.get("is_achieved"):
                    # 4. Мутация состояния: чекпоинт достигнут
                    current_checkpoint.is_completed = True
                    db.add(current_checkpoint)
                    await db.commit()
                    print(f"[Director] Checkpoint {current_checkpoint.order_num} achieved for chat {chat_id}!")

            except Exception as e:
                print(f"[Director] Error checking progress: {e}")

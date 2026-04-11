from typing import List, Optional, Any
from uuid import UUID
from fastapi import BackgroundTasks
from shared.base.service import BaseService
from .repository import ChatRepository
from .models import Chat
from app.schemas.chat import ChatCreate, ChatUpdate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

class ChatService(BaseService[ChatRepository]):
    async def create_chat(self, chat_in: ChatCreate, user_id: UUID, background_tasks: BackgroundTasks, db: AsyncSession) -> Chat:
        # We pass db here temporarily if needed for complex cross-service logic, 
        # but ideally we should use injected repositories.
        from app.domains.character.models import Character
        from app.domains.persona.models import UserPersona
        from app.domains.scenario.models import Scenario

        character = await db.get(Character, chat_in.character_id)
        if not character:
            raise ValueError("Character not found")

        persona = await db.get(UserPersona, chat_in.user_persona_id)
        if not persona:
            raise ValueError("Persona not found")

        if str(persona.owner_id) != str(user_id):
            raise PermissionError("You can only use your own personas")

        scenario = None
        if chat_in.scenario_id:
            scenario = await db.get(Scenario, chat_in.scenario_id)
            if not scenario:
                raise ValueError("Scenario not found")

        chat = Chat(
            user_id=user_id,
            character_id=character.id,
            user_persona_id=persona.id,
            scenario_id=scenario.id if scenario else None,
            mode="scenario" if scenario else "sandbox",
            is_acquainted=chat_in.is_acquainted,
            relationship_dynamic=chat_in.relationship_dynamic,
            language=chat_in.language,
            narrative_voice=chat_in.narrative_voice,
        )

        created_chat = await self.repository.create(obj_in=chat)
        
        # Increment character chat count
        character.total_chats_count += 1
        await db.commit()
        await db.refresh(created_chat)

        if created_chat.mode == "scenario":
            from app.core.director_service import DirectorService
            director = DirectorService()
            cp_count = max(2, min(6, chat_in.checkpoints_count))
            background_tasks.add_task(director.initialize_scenario, created_chat.id, cp_count)

        return created_chat

    async def get_user_chats(self, user_id: UUID, skip: int = 0, limit: int = 20) -> List[Chat]:
        return await self.repository.get_by_user(user_id, skip, limit)

    async def get_chat(self, chat_id: UUID, user_id: UUID) -> Optional[Chat]:
        chat = await self.repository.get(chat_id)
        if chat and str(chat.user_id) == str(user_id):
            return chat
        return None

    async def update_chat(self, chat_id: UUID, chat_update: ChatUpdate, user_id: UUID) -> Optional[Chat]:
        chat = await self.get_chat(chat_id, user_id)
        if not chat:
            return None
        return await self.repository.update(db_obj=chat, obj_in=chat_update)

    async def delete_chat(self, chat_id: UUID, user_id: UUID) -> bool:
        chat = await self.get_chat(chat_id, user_id)
        if not chat:
            return False
        await self.repository.delete(id=chat_id)
        return True

    async def get_history_payload(self, chat_id: UUID, user_id: UUID, db: AsyncSession) -> dict:
        from app.domains.chat.message_models import Message
        from app.domains.chat.models import ChatCheckpoint
        from collections import defaultdict

        chat = await self.get_chat(chat_id, user_id)
        if not chat:
            raise ValueError("Chat not found")

        # Checkpoints
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

        # Messages
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

        children_map = defaultdict(list)
        msg_dict = {}
        for m in all_msgs:
            children_map[m.parent_id].append(m)
            msg_dict[m.id] = m

        for siblings in children_map.values():
            siblings.sort(key=lambda x: x.created_at)

        def _build_node(msg):
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
                "children_ids": [c.id for c in children_map.get(msg.id, [])],
            }

        tree = [_build_node(m) for m in all_msgs]

        leaf_id = chat.active_leaf_id
        if not leaf_id or leaf_id not in msg_dict:
            leaves = [m for m in all_msgs if not children_map.get(m.id)]
            leaf_id = leaves[-1].id if leaves else all_msgs[-1].id

        branch = []
        curr_id = leaf_id
        while curr_id:
            m = msg_dict.get(curr_id)
            if not m: break
            branch.append(_build_node(m))
            curr_id = m.parent_id
        branch.reverse()

        return {
            "active_leaf_id": leaf_id,
            "active_branch": branch,
            "tree": tree,
            "checkpoints": checkpoints_list
        }

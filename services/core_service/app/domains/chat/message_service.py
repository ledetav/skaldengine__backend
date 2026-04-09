from typing import List, Optional, Any
from uuid import UUID
from fastapi import BackgroundTasks
from shared.base.service import BaseService
from .message_repository import MessageRepository
from .models import Chat
from .message_models import Message
from .message_schemas import MessageCreate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update as sa_update

class MessageService(BaseService[MessageRepository]):
    async def send_message_stream(
        self, chat_id: UUID, user_id: UUID, message_in: MessageCreate, 
        background_tasks: BackgroundTasks, db: AsyncSession
    ):
        from .models import Chat
        from ..character.models import Character
        from ..persona.models import UserPersona
        from ..scenario.models import Scenario

        chat = await db.get(Chat, chat_id)
        if not chat or str(chat.user_id) != str(user_id):
            raise ValueError("Chat not found")

        # Save user message
        user_msg = Message(
            chat_id=chat.id,
            role="user",
            content=message_in.content,
            parent_id=message_in.parent_id,
        )
        db.add(user_msg)
        
        if not chat.title and not message_in.parent_id:
            from app.core.title_service import ChatTitleService
            title_service = ChatTitleService()
            background_tasks.add_task(title_service.generate_and_update_title, db, chat.id, message_in.content)

        await db.commit()
        await db.refresh(user_msg)

        # Build payload
        from app.core.prompt_pipeline import PromptPipeline
        pipeline = PromptPipeline(db, chat_id, user_id=user_id, parent_id=message_in.parent_id)
        payload = await pipeline.build_payload(message_in.content)
        
        # AI message template
        ai_msg = Message(
            chat_id=chat.id,
            role="assistant",
            content="",
            parent_id=user_msg.id,
        )
        db.add(ai_msg)
        await db.flush()

        # Update active leaf
        await db.execute(
            sa_update(Chat)
            .where(Chat.id == chat.id)
            .values(active_leaf_id=ai_msg.id)
        )
        await db.commit()
        await db.refresh(ai_msg)

        # Streaming
        from app.api.endpoints.stream_utils import generate_chat_stream
        state = {}
        return generate_chat_stream(chat.id, ai_msg.id, payload, state)

    async def regenerate_stream(self, parent_id: UUID, user_id: UUID, db: AsyncSession):
        parent_msg = await self.repository.get(parent_id)
        if not parent_msg or parent_msg.role != "user":
            raise ValueError("Parent user message not found")
            
        chat = await db.get(Chat, parent_msg.chat_id)
        if not chat or str(chat.user_id) != str(user_id):
            raise ValueError("Chat not found")

        from app.core.prompt_pipeline import PromptPipeline
        pipeline = PromptPipeline(db, chat.id, user_id=user_id, parent_id=parent_id)
        payload = await pipeline.build_payload(parent_msg.content)
        
        ai_msg = Message(
            chat_id=chat.id,
            role="assistant",
            content="",
            parent_id=parent_id,
        )
        db.add(ai_msg)
        await db.flush()

        await db.execute(
            sa_update(Chat)
            .where(Chat.id == chat.id)
            .values(active_leaf_id=ai_msg.id)
        )
        await db.commit()
        await db.refresh(ai_msg)

        from app.api.endpoints.stream_utils import generate_chat_stream
        state = {}
        return generate_chat_stream(chat.id, ai_msg.id, payload, state)

    async def edit_message(self, message_id: UUID, new_content: str, user_id: UUID, db: AsyncSession) -> Message:
        original_msg = await self.repository.get(message_id)
        if not original_msg:
            raise ValueError("Message not found")
            
        chat = await db.get(Chat, original_msg.chat_id)
        if not chat or str(chat.user_id) != str(user_id):
            raise ValueError("Chat not found")
            
        new_msg = Message(
            chat_id=chat.id,
            role=original_msg.role,
            content=new_content,
            parent_id=original_msg.parent_id,
            is_edited=True
        )
        db.add(new_msg)
        await db.flush()

        await db.execute(
            sa_update(Chat)
            .where(Chat.id == chat.id)
            .values(active_leaf_id=new_msg.id)
        )
        await db.commit()
        await db.refresh(new_msg)
        return new_msg

    async def fork_chat(self, message_id: UUID, user_id: UUID, db: AsyncSession) -> Chat:
        from app.models.episodic_memory import EpisodicMemory
        from app.models.chat_checkpoint import ChatCheckpoint
        from sqlalchemy import cast as sql_cast

        target_msg = await self.repository.get(message_id)
        if not target_msg:
            raise ValueError("Message not found")
            
        original_chat = await db.get(Chat, target_msg.chat_id)
        if not original_chat or str(original_chat.user_id) != str(user_id):
            raise PermissionError("Forbidden")

        new_chat = Chat(
            user_id=user_id,
            character_id=original_chat.character_id,
            user_persona_id=original_chat.user_persona_id,
            mode=original_chat.mode,
            scenario_id=original_chat.scenario_id,
            is_acquainted=original_chat.is_acquainted,
            relationship_dynamic=original_chat.relationship_dynamic,
            language=original_chat.language,
            narrative_voice=original_chat.narrative_voice,
            persona_lorebook_id=original_chat.persona_lorebook_id
        )
        db.add(new_chat)
        await db.flush()

        # Path to root
        path = []
        curr = target_msg
        while curr:
            path.append(curr)
            if not curr.parent_id: break
            curr = await self.repository.get(curr.parent_id)
        path.reverse()

        old_to_new = {}
        last_id = None
        for m in path:
            cloned = Message(
                chat_id=new_chat.id,
                role=m.role,
                content=m.content,
                hidden_thought=m.hidden_thought,
                is_edited=m.is_edited,
                parent_id=last_id,
                created_at=m.created_at
            )
            db.add(cloned)
            await db.flush()
            old_to_new[m.id] = cloned.id
            last_id = cloned.id

        new_chat.active_leaf_id = last_id

        # Episodic memory
        mem_res = await db.execute(
            select(EpisodicMemory).where(EpisodicMemory.message_id.in_(old_to_new.keys()))
        )
        for mem in mem_res.scalars().all():
            db.add(EpisodicMemory(
                chat_id=new_chat.id,
                message_id=old_to_new[mem.message_id],
                summary=mem.summary,
                embedding=mem.embedding
            ))

        # Checkpoints
        if original_chat.mode == "scenario":
            cp_res = await db.execute(select(ChatCheckpoint).where(ChatCheckpoint.chat_id == original_chat.id))
            for cp in cp_res.scalars().all():
                db.add(ChatCheckpoint(
                    chat_id=new_chat.id,
                    order_num=cp.order_num,
                    goal_description=cp.goal_description,
                    is_completed=cp.is_completed,
                    messages_spent=cp.messages_spent
                ))

        await db.commit()
        await db.refresh(new_chat)
        return new_chat

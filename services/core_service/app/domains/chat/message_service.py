"""
Сервисный слой для потоковой обработки сообщений (Message), ветвления, редактирования и форка чатов.
"""

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
    """
    Сервис сообщений: потоковая генерация SSE через LLM-пайплайн, свайпы (регенерация),
    редактирование сообщений и форк ветки в новую игровую сессию.
    """
    async def send_message_stream(
        self, chat_id: UUID, current_user: Any, message_in: MessageCreate, 
        background_tasks: BackgroundTasks, db: AsyncSession
    ):
        """
        Сохранение сообщения пользователя, обновление чекпоинтов,
        сборка системного промпта через PromptPipeline и запуск SSE-стриминга ответа ИИ.
        """
        from .models import Chat
        from app.domains.character.models import Character
        from app.domains.persona.models import UserPersona
        from app.domains.scenario.models import Scenario

        chat = await db.get(Chat, chat_id)
        if not chat or str(chat.user_id) != str(current_user.id):
            raise ValueError("Chat not found")

        # Сохранение входящего сообщения пользователя
        user_msg = Message(
            chat_id=chat.id,
            role="user",
            content=message_in.content,
            parent_id=message_in.parent_id,
        )
        db.add(user_msg)
        
        # Автоматическая генерация заголовка для нового чата
        if not chat.title and not message_in.parent_id:
            from app.core.title_service import ChatTitleService
            title_service = ChatTitleService()
            background_tasks.add_task(title_service.generate_and_update_title, chat.id, message_in.content)

        await db.commit()
        await db.refresh(user_msg)

        # Увеличение счетчика сообщений для активной контрольной точки
        from .models import ChatCheckpoint
        cp_stmt = (
            select(ChatCheckpoint)
            .where(ChatCheckpoint.chat_id == chat.id, ChatCheckpoint.is_completed == False)
            .order_by(ChatCheckpoint.order_num)
        )
        cp_res = await db.execute(cp_stmt)
        active_cp = cp_res.scalars().first()
        if active_cp:
            active_cp.messages_spent += 1
            db.add(active_cp)
            await db.commit()

        # Сборка промпта через конвейер стадий
        from app.core.prompt_pipeline import PromptPipeline
        pipeline = PromptPipeline(db, chat_id, current_user=current_user, parent_id=message_in.parent_id)
        payload = await pipeline.build_payload(message_in.content)
        
        # Шаблон сообщения ассистента в БД
        ai_msg = Message(
            chat_id=chat.id,
            role="assistant",
            content="",
            parent_id=user_msg.id,
        )
        db.add(ai_msg)
        await db.flush()

        # Обновление указателя активного листа чата
        await db.execute(
            sa_update(Chat)
            .where(Chat.id == chat.id)
            .values(active_leaf_id=ai_msg.id)
        )
        await db.commit()
        await db.refresh(ai_msg)

        # Запуск стриминга ответа через Polza API / локальный провайдер
        from app.api.endpoints.stream_utils import generate_chat_stream
        state = {}

        return generate_chat_stream(chat.id, ai_msg.id, payload, state)

    async def regenerate_stream(self, parent_id: UUID, current_user: Any, db: AsyncSession):
        """
        Перегенерация ответа ИИ для указанного сообщения пользователя (механика свайпа).
        """
        parent_msg = await self.repository.get(parent_id)
        if not parent_msg or parent_msg.role != "user":
            raise ValueError("Parent user message not found")
            
        chat = await db.get(Chat, parent_msg.chat_id)
        if not chat or str(chat.user_id) != str(current_user.id):
            raise ValueError("Chat not found")

        from app.core.prompt_pipeline import PromptPipeline
        pipeline = PromptPipeline(db, chat.id, current_user=current_user, parent_id=parent_id)
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
        """
        Редактирование сообщения в истории.
        Создает новое сообщение-потомок того же родителя (непрямое ветвление), сохраняя историю.
        """
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
        """
        Явное форкание (ответвление) диалога в новый независимый чат.
        Копирует всю цепочку сообщений от корня до выбранного узла,
        включая эпизодическую память и контрольные точки сценария.
        """
        from app.domains.chat.models import EpisodicMemory
        from app.domains.chat.models import ChatCheckpoint
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

        # Восстановление пути от целевого сообщения к корню
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

        # Клонирование эпизодической памяти
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

        # Клонирование контрольных точек сценария
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

    async def get_message(self, message_id: UUID, user_id: UUID, db: AsyncSession) -> Optional[Message]:
        """Получить сообщение по ID с проверкой прав доступа к чату."""
        message = await self.repository.get(message_id)
        if not message:
            return None
        chat = await db.get(Chat, message.chat_id)
        if not chat or str(chat.user_id) != str(user_id):
            return None
        return message

    async def delete_message(self, message_id: UUID, user_id: UUID, db: AsyncSession) -> bool:
        """Удалить сообщение из чата с проверкой прав владельца."""
        message = await self.repository.get(message_id)
        if not message:
            return False
        chat = await db.get(Chat, message.chat_id)
        if not chat or str(chat.user_id) != str(user_id):
            return False
        await self.repository.delete(id=message_id)
        return True


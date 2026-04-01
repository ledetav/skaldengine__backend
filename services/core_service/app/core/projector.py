import json
import asyncio
import logging
import uuid
from datetime import datetime
from aiokafka import AIOKafkaConsumer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.base import AsyncSessionLocal
from app.models.session import Session
from app.models.message import Message

logger = logging.getLogger("projector")

def to_uuid(val: str | None) -> uuid.UUID | None:
    """Безопасная конвертация строки в UUID"""
    if not val:
        return None
    return uuid.UUID(str(val))

def to_datetime(val: str | None) -> datetime | None:
    """Безопасная конвертация ISO-строки в datetime"""
    if not val:
        return None
    if isinstance(val, str):
        # Заменяем Z на +00:00 для совместимости форматов
        return datetime.fromisoformat(val.replace('Z', '+00:00'))
    return val

async def process_event(event_data: dict, db: AsyncSession):
    event_type = event_data.get("event_type")
    entity_id_str = event_data.get("entity_id")
    
    if not event_type or not entity_id_str:
        return

    entity_id = to_uuid(entity_id_str)

    # 1. Обработка создания сессии
    if event_type == "SessionCreated":
        existing = await db.execute(select(Session).where(Session.id == entity_id))
        if existing.scalar_one_or_none():
            return 
            
        new_session = Session(
            id=entity_id,
            user_id=to_uuid(event_data.get("user_id")),
            character_id=to_uuid(event_data.get("character_id")),
            persona_id=to_uuid(event_data.get("persona_id")),
            scenario_id=to_uuid(event_data.get("scenario_id")),
            mode=event_data.get("mode"),
            language=event_data.get("language"),
            speech_style=event_data.get("speech_style"),
            character_name_snapshot=event_data.get("character_name_snapshot"),
            persona_name_snapshot=event_data.get("persona_name_snapshot"),
            relationship_context=event_data.get("relationship_context"),
            cached_system_prompt=event_data.get("cached_system_prompt"),
            current_step=0,
            created_at=to_datetime(event_data.get("timestamp"))
        )
        db.add(new_session)
        await db.commit()
        logger.info(f"[Projector] Session {entity_id} saved to Read Model.")

    # 2. Обработка добавления сообщения
    elif event_type == "MessageAdded":
        existing = await db.execute(select(Message).where(Message.id == entity_id))
        if existing.scalar_one_or_none():
            return
            
        new_msg = Message(
            id=entity_id,
            session_id=to_uuid(event_data.get("session_id")),
            parent_id=to_uuid(event_data.get("parent_id")),
            role=event_data.get("role"),
            content=event_data.get("content"),
            is_active=True,
            created_at=to_datetime(event_data.get("timestamp"))
        )
        db.add(new_msg)
        
        session = await db.get(Session, to_uuid(event_data.get("session_id")))
        if session:
            session.updated_at = to_datetime(event_data.get("timestamp"))
            db.add(session)
            
        await db.commit()
        logger.info(f"[Projector] Message {entity_id} saved to Read Model.")

async def consume_events_forever():
    consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC_EVENTS,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="core_service_read_model_projector", 
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset="earliest"
    )
    
    while True:
        try:
            await consumer.start()
            logger.info("🎧 Read Model Projector successfully connected to Kafka!")
            break
        except Exception as e:
            logger.warning(f"⏳ Waiting for Kafka to be ready... ({e})")
            await asyncio.sleep(3)
            
    try:
        async for msg in consumer:
            event_data = msg.value
            try:
                async with AsyncSessionLocal() as db:
                    await process_event(event_data, db)
            except Exception as e:
                logger.error(f"Error processing event {event_data.get('event_id')}: {e}")
    except asyncio.CancelledError:
        logger.info("🛑 Projector task was cancelled.")
    finally:
        await consumer.stop()
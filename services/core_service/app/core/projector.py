import json
import asyncio
import logging
from aiokafka import AIOKafkaConsumer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.base import AsyncSessionLocal
from app.models.session import Session
from app.models.message import Message

logger = logging.getLogger("projector")

async def process_event(event_data: dict, db: AsyncSession):
    """
    Машрутизатор событий. Берет сырой JSON из Kafka и применяет его к БД (Read Model).
    """
    event_type = event_data.get("event_type")
    entity_id = event_data.get("entity_id")
    
    if not event_type or not entity_id:
        return

    if event_type == "SessionCreated":
        # Проверка на идемпотентность (вдруг событие пришло дважды)
        existing = await db.execute(select(Session).where(Session.id == entity_id))
        if existing.scalar_one_or_none():
            return  # Уже обработано
            
        new_session = Session(
            id=entity_id,
            user_id=event_data.get("user_id"),
            character_id=event_data.get("character_id"),
            persona_id=event_data.get("persona_id"),
            scenario_id=event_data.get("scenario_id"),
            mode=event_data.get("mode"),
            language=event_data.get("language"),
            speech_style=event_data.get("speech_style"),
            character_name_snapshot=event_data.get("character_name_snapshot"),
            persona_name_snapshot=event_data.get("persona_name_snapshot"),
            relationship_context=event_data.get("relationship_context"),
            cached_system_prompt=event_data.get("cached_system_prompt"),
            current_step=0,
            created_at=event_data.get("timestamp")
        )
        db.add(new_session)
        await db.commit()
        logger.info(f"[Projector] Session {entity_id} saved to Read Model.")

    elif event_type == "MessageAdded":
        existing = await db.execute(select(Message).where(Message.id == entity_id))
        if existing.scalar_one_or_none():
            return
            
        new_msg = Message(
            id=entity_id,
            session_id=event_data.get("session_id"),
            parent_id=event_data.get("parent_id"),
            role=event_data.get("role"),
            content=event_data.get("content"),
            is_active=True,
            created_at=event_data.get("timestamp")
        )
        db.add(new_msg)
        
        # Обновляем время активности сессии
        session = await db.get(Session, event_data.get("session_id"))
        if session:
            session.updated_at = event_data.get("timestamp")
            db.add(session)
            
        await db.commit()
        logger.info(f"[Projector] Message {entity_id} saved to Read Model.")

async def consume_events_forever():
    """
    Бесконечный цикл чтения Kafka.
    """
    consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC_EVENTS,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="core_service_read_model_projector", # Свой уникальный consumer group
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset="earliest" # При первом запуске вычитает всё с самого начала
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
                # Каждое событие обрабатываем в отдельной транзакции БД
                async with AsyncSessionLocal() as db:
                    await process_event(event_data, db)
            except Exception as e:
                logger.error(f"Error processing event {event_data.get('event_id')}: {e}")
                # В продакшене здесь обычно отправляют событие в Dead Letter Queue (DLQ)
    except asyncio.CancelledError:
        logger.info("🛑 Projector task was cancelled.")
    finally:
        await consumer.stop()
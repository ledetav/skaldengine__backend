import json
import asyncio
import logging
import uuid
from aiokafka import AIOKafkaConsumer
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.base import AsyncSessionLocal
from app.models.outbox_event import OutboxEvent
from app.models.processed_event import ProcessedEvent
from app.models.session import Session
from app.models.message import Message
from app.models.user_persona import UserPersona

logger = logging.getLogger("core_saga")

async def process_auth_event(event_data: dict, db: AsyncSession):
    event_id_str = event_data.get("event_id")
    event_type = event_data.get("event_type")
    aggregate_id_str = event_data.get("aggregate_id")
    
    if not event_id_str or not event_type or not aggregate_id_str:
        return

    event_id = uuid.UUID(event_id_str)
    user_id = uuid.UUID(aggregate_id_str)

    existing_event = await db.get(ProcessedEvent, event_id)
    if existing_event:
        logger.info(f"Event {event_id} already processed. Skipping.")
        return

    if event_type == "UserDeletionRequested":
        logger.info(f"Starting data purge for user {user_id}")
        
        sessions_query = await db.execute(select(Session.id).where(Session.user_id == user_id))
        session_ids = sessions_query.scalars().all()
        
        if session_ids:

            await db.execute(delete(Message).where(Message.session_id.in_(session_ids)))
        
        await db.execute(delete(Session).where(Session.user_id == user_id))
        
        await db.execute(delete(UserPersona).where(UserPersona.owner_id == user_id))
        
        outbox_event = OutboxEvent(
            aggregate_type="User",
            aggregate_id=str(user_id),
            event_type="UserCoreDataPurged",
            payload={"status": "success", "purged_sessions": len(session_ids)}
        )
        db.add(outbox_event)

        processed = ProcessedEvent(id=event_id, topic=settings.KAFKA_TOPIC_AUTH_EVENTS)
        db.add(processed)

        await db.commit()
        logger.info(f"Successfully purged core data for user {user_id} and scheduled UserCoreDataPurged.")

async def consume_auth_events_forever():
    consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC_AUTH_EVENTS,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="core_service_saga_group",
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset="earliest"
    )
    
    while True:
        try:
            await consumer.start()
            logger.info("🎧 Core Saga Consumer connected to Auth Events!")
            break
        except Exception as e:
            logger.warning(f"⏳ Waiting for Kafka... ({e})")
            await asyncio.sleep(3)
            
    try:
        async for msg in consumer:
            event_data = msg.value
            try:
                async with AsyncSessionLocal() as db:
                    await process_auth_event(event_data, db)
            except Exception as e:
                logger.error(f"Error processing auth event {event_data.get('event_id')}: {e}")
    except asyncio.CancelledError:
        logger.info("🛑 Core Saga Consumer cancelled.")
    finally:
        await consumer.stop()
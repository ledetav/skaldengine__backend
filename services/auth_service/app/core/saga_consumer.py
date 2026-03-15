import json
import asyncio
import logging
import uuid
from aiokafka import AIOKafkaConsumer
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.base import AsyncSessionLocal
from app.models.processed_event import ProcessedEvent
from app.models.user import User

logger = logging.getLogger("auth_saga")

async def process_core_event(event_data: dict, db: AsyncSession):
    event_id_str = event_data.get("event_id") or event_data.get("id") 
    event_type = event_data.get("event_type")
    aggregate_id_str = event_data.get("aggregate_id")
    
    if not event_id_str or not event_type or not aggregate_id_str:
        return

    event_id = uuid.UUID(str(event_id_str))
    user_id = uuid.UUID(str(aggregate_id_str))

    existing_event = await db.get(ProcessedEvent, event_id)
    if existing_event:
        logger.info(f"Event {event_id} already processed. Skipping.")
        return

    if event_type == "UserCoreDataPurged":
        logger.info(f"Received confirmation of core data purge for user {user_id}. Finalizing deletion.")
        
        await db.execute(delete(User).where(User.id == user_id))
        
        processed = ProcessedEvent(id=event_id, topic=settings.KAFKA_TOPIC_CORE_EVENTS)
        db.add(processed)
        
        await db.commit()
        logger.info(f"✅ Successfully deleted user {user_id} from Auth Service. Saga completed.")

async def consume_core_events_forever():
    consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC_CORE_EVENTS,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="auth_service_saga_group",
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset="earliest"
    )
    
    while True:
        try:
            await consumer.start()
            logger.info("🎧 Auth Saga Consumer connected to Core Events!")
            break
        except Exception as e:
            logger.warning(f"⏳ Waiting for Kafka... ({e})")
            await asyncio.sleep(3)
            
    try:
        async for msg in consumer:
            if isinstance(msg.value, dict) and msg.value.get("event_type") == "UserCoreDataPurged":
                try:
                    async with AsyncSessionLocal() as db:
                        await process_core_event(msg.value, db)
                except Exception as e:
                    logger.error(f"Error processing core event: {e}")
    except asyncio.CancelledError:
        logger.info("🛑 Auth Saga Consumer cancelled.")
    finally:
        await consumer.stop()
import json
import asyncio
import logging
from aiokafka import AIOKafkaConsumer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.base import AsyncSessionLocal

logger = logging.getLogger("core_events")

async def process_domain_event(event_data: dict, db: AsyncSession):
    """
    Обработка доменных событий для внутренних нужд Core Service.
    Например, обновление статистики, логирование, кэширование и т.д.
    """
    event_type = event_data.get("event_type")
    entity_type = event_data.get("entity_type")
    entity_id = event_data.get("entity_id")
    
    if not event_type or not entity_id:
        return
    
    # Пример обработки событий (можно расширить по необходимости)
    if entity_type == "Session" and event_type == "Created":
        logger.info(f"New session created: {entity_id}")
        # Здесь можно добавить логику обновления статистики, кэширования и т.д.
        
    elif entity_type == "Message" and event_type == "Added":
        logger.info(f"New message added to session: {event_data.get('session_id')}")
        # Можно обновить счетчики сообщений, последнюю активность и т.д.
        
    elif entity_type == "Character" and event_type == "Created":
        logger.info(f"New character created: {entity_id}")
        
    elif entity_type == "Persona" and event_type == "Created":
        logger.info(f"New persona created: {entity_id}")
        
    # Добавить другие типы событий по мере необходимости

async def consume_domain_events_forever():
    """
    Фоновая задача для прослушивания доменных событий Core Service.
    Используется для внутренних нужд: статистика, логирование, кэширование.
    """
    consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC_EVENTS,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="core_service_domain_events_group",
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset="earliest"
    )
    
    while True:
        try:
            await consumer.start()
            logger.info("🎧 Core Service Domain Events Consumer connected!")
            break
        except Exception as e:
            logger.warning(f"⏳ Waiting for Kafka... ({e})")
            await asyncio.sleep(3)
            
    try:
        async for msg in consumer:
            event_data = msg.value
            try:
                async with AsyncSessionLocal() as db:
                    await process_domain_event(event_data, db)
            except Exception as e:
                logger.error(f"Error processing domain event {event_data.get('event_id')}: {e}")
    except asyncio.CancelledError:
        logger.info("🛑 Core Domain Events Consumer cancelled.")
    finally:
        await consumer.stop()
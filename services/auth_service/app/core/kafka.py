import asyncio
import json
import logging
from aiokafka import AIOKafkaProducer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.base import AsyncSessionLocal
from app.models.outbox import OutboxEvent

logger = logging.getLogger("auth_kafka")

producer: AIOKafkaProducer | None = None

async def get_kafka_producer() -> AIOKafkaProducer:
    global producer
    if producer is None:
        producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await producer.start()
        logger.info("Auth Kafka Producer started")
    return producer

async def close_kafka_producer():
    global producer
    if producer:
        await producer.stop()
        logger.info("Auth Kafka Producer stopped")

async def outbox_relay_worker():
    """Фоновый процесс, который читает непрочитанные события из БД и шлет в Kafka"""
    while True:
        try:
            prod = await get_kafka_producer()
            async with AsyncSessionLocal() as db:
                # Ищем непроцесснутые события
                query = select(OutboxEvent).where(OutboxEvent.processed == False).order_by(OutboxEvent.created_at.asc()).limit(50)
                result = await db.execute(query)
                events = result.scalars().all()

                for event in events:
                    message = {
                        "event_id": str(event.id),
                        "aggregate_type": event.aggregate_type,
                        "aggregate_id": event.aggregate_id,
                        "event_type": event.event_type,
                        "payload": event.payload,
                        "timestamp": event.created_at.isoformat()
                    }
                    
                    # Отправляем в Kafka (используем aggregate_id как ключ для сохранения порядка)
                    await prod.send_and_wait(
                        topic=settings.KAFKA_TOPIC_AUTH_EVENTS,
                        value=message,
                        key=event.aggregate_id.encode('utf-8')
                    )
                    
                    event.processed = True
                    db.add(event)
                
                if events:
                    await db.commit()
                    logger.info(f"Processed {len(events)} outbox events")
                    
        except Exception as e:
            logger.error(f"Auth Outbox Relay Error: {e}")
        
        await asyncio.sleep(2)
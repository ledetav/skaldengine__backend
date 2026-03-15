import json
from datetime import datetime, timezone
from aiokafka import AIOKafkaProducer
from app.core.config import settings
from app.schemas.events import BaseEvent
import logging

import asyncio
from sqlalchemy import select
from app.db.base import AsyncSessionLocal
from app.models.outbox_event import OutboxEvent

logger = logging.getLogger(__name__)

producer: AIOKafkaProducer | None = None

async def get_kafka_producer() -> AIOKafkaProducer:
    """Инициализация и получение инстанса Kafka Producer"""
    global producer
    if producer is None:
        producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            # Сериализуем dict в JSON, а затем в байты
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await producer.start()
        logger.info("Kafka Producer started")
    return producer

async def close_kafka_producer():
    """Закрытие соединения с Kafka"""
    global producer
    if producer:
        await producer.stop()
        logger.info("Kafka Producer stopped")

async def send_entity_event(event_type: str, entity_type: str, entity_id: str, payload: dict = None):
    """
    Универсальная функция для отправки событий.
    event_type: Created, Updated, Deleted
    entity_type: Character, Session, Persona
    """
    global producer
    if not producer:
        logger.warning("Kafka Producer is not initialized!")
        return

    message = {
        "event": f"{entity_type}{event_type}",
        "event_type": event_type,
        "entity_type": entity_type,
        "entity_id": str(entity_id),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": payload or {}
    }
    
    try:
        await producer.send_and_wait(settings.KAFKA_TOPIC_EVENTS, message)
        logger.info(f"Published event: {message['event']} for ID {entity_id}")
    except Exception as e:
        logger.error(f"Failed to publish event to Kafka: {e}")

async def publish_domain_event(event: BaseEvent, topic: str = settings.KAFKA_TOPIC_EVENTS):
    """
    Отправка типизированного события для Event Sourcing.
    Используем entity_id как ключ партицирования, чтобы события одной сессии 
    всегда приходили в строгом хронологическом порядке.
    """
    global producer
    if not producer:
        logger.warning("Kafka Producer is not initialized!")
        return

    # Сериализуем Pydantic модель в JSON
    event_dict = event.model_dump(mode='json')
    
    try:
        # Передаем ключ (key), чтобы Kafka гарантировала порядок событий для одной сущности
        key = str(event.entity_id).encode('utf-8')
        
        await producer.send_and_wait(
            topic, 
            value=event_dict,
            key=key 
        )
        logger.info(f"Published Event Sourcing event: {event.event_type} for Entity {event.entity_id}")
    except Exception as e:
        logger.error(f"Failed to publish event to Kafka: {e}")

async def core_outbox_relay_worker():
    """Фоновый процесс, который читает непрочитанные события из БД и шлет в Kafka"""
    while True:
        try:
            prod = await get_kafka_producer()
            async with AsyncSessionLocal() as db:
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
                    
                    # Core будет отвечать в этот же топик, либо можно завести отдельный.
                    # Будем использовать общий топик ивентов для упрощения.
                    await prod.send_and_wait(
                        topic=settings.KAFKA_TOPIC_EVENTS,
                        value=message,
                        key=event.aggregate_id.encode('utf-8')
                    )
                    
                    event.processed = True
                    db.add(event)
                
                if events:
                    await db.commit()
                    
        except Exception as e:
            logger.error(f"Core Outbox Relay Error: {e}")
        
        await asyncio.sleep(2)
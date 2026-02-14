import json
from aiokafka import AIOKafkaProducer
from app.core.config import settings
import logging

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
        "entity_type": entity_type,
        "entity_id": str(entity_id),
        "payload": payload or {}
    }
    
    try:
        await producer.send_and_wait(settings.KAFKA_TOPIC_EVENTS, message)
        logger.info(f"Published event: {message['event']} for ID {entity_id}")
    except Exception as e:
        logger.error(f"Failed to publish event to Kafka: {e}")
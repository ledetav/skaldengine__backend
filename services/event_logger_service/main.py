import json
import asyncio
import logging
import os
from aiokafka import AIOKafkaConsumer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("event_logger")

# Внутри Docker Compose сеть другая, поэтому обращаемся по имени контейнера "kafka"
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "skaldenginebackend-kafka:9092")
KAFKA_TOPIC_EVENTS = os.getenv("KAFKA_TOPIC_EVENTS", "skaldenginebackend_entity_events")

async def consume_events():
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC_EVENTS,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="skald-logging-group",
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset="earliest"
    )
    
    while True:
        try:
            await consumer.start()
            logger.info("🎧 Event Logger successfully connected to Kafka!")
            break
        except Exception as e:
            logger.warning(f"⏳ Waiting for Kafka to be ready... ({e})")
            await asyncio.sleep(3)
    
    try:
        async for msg in consumer:
            event_data = msg.value
            logger.info("\n" + "="*50)
            logger.info(f"📥 [KAFKA EVENT] Topic: {msg.topic}")
            logger.info(f"🏷️  Event: {event_data.get('event')}")
            logger.info(f"🆔  Entity ID: {event_data.get('entity_id')}")
            logger.info(f"📦  Payload: {json.dumps(event_data.get('payload', {}), indent=2, ensure_ascii=False)}")
            logger.info("="*50 + "\n")
    except asyncio.CancelledError:
        logger.info("🛑 Consumer task was cancelled.")
    finally:
        await consumer.stop()

if __name__ == "__main__":
    asyncio.run(consume_events())
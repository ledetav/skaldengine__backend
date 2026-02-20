import asyncio
import json
import logging
from sqlalchemy import text
from aiokafka import AIOKafkaConsumer, TopicPartition

from app.core.config import settings
from app.db.base import AsyncSessionLocal
from app.core.projector import process_event

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("replay_script")

async def replay_all_events():
    logger.info("🚀 Starting Full Replay of Read Model from Kafka...")

    async with AsyncSessionLocal() as db:
        await db.execute(text("TRUNCATE TABLE messages CASCADE;"))
        await db.execute(text("TRUNCATE TABLE sessions CASCADE;"))
        await db.commit()
        logger.info("🧹 Read Model (PostgreSQL tables) truncated successfully.")
 
    consumer = AIOKafkaConsumer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset="earliest"
    )

    try:
        await consumer.start()
        
        topic = settings.KAFKA_TOPIC_EVENTS
        
        await consumer._client.force_metadata_update()
        await asyncio.sleep(0.5)

        topic_partitions = consumer.partitions_for_topic(topic)
        
        if not topic_partitions:
            logger.info("⚠️ No partitions found. Topic might be empty or not created yet.")
            return
            
        partitions = [TopicPartition(topic, p) for p in topic_partitions]
        consumer.assign(partitions)

        end_offsets = await consumer.end_offsets(partitions)

        has_messages = any(offset > 0 for offset in end_offsets.values())
        if not has_messages:
            logger.info("📭 Kafka topic is empty. Nothing to replay.")
            return

        await consumer.seek_to_beginning()

        events_processed = 0

        while True:
            reached_end = True
            for p in partitions:
                if await consumer.position(p) < end_offsets[p]:
                    reached_end = False
                    break

            if reached_end:
                break

            batch = await consumer.getmany(timeout_ms=2000, max_records=200)
            if not batch:
                break

            async with AsyncSessionLocal() as db:
                for tp, messages in batch.items():
                    for msg in messages:
                        if msg.value.get("event_type") in ["SessionCreated", "MessageAdded", "MessageDeactivated", "MessageEdited"]:
                            await process_event(msg.value, db)
                            events_processed += 1
                await db.commit()

        logger.info(f"✅ Replay completed successfully! Reconstructed state from {events_processed} events.")

    except Exception as e:
        logger.error(f"❌ Error during replay: {e}")
    finally:
        try:
            await consumer.stop()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(replay_all_events())

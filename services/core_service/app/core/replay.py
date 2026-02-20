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

    # Удаляем только проекции Event Sourcing. Юзеров, персонажей и лор не трогаем!
    async with AsyncSessionLocal() as db:
        await db.execute(text("TRUNCATE TABLE messages CASCADE;"))
        await db.execute(text("TRUNCATE TABLE sessions CASCADE;"))
        await db.commit()
        logger.info("🧹 Read Model (PostgreSQL tables) truncated successfully.")
 
    # НЕ указываем group_id, чтобы консьюмер был анонимным и читал всё с самого начала
    # НЕ указываем топик в конструкторе, т.к. будем использовать assign() вручную
    consumer = AIOKafkaConsumer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset="earliest"
    )

    try:
        await consumer.start()
        
        # Принудительно получаем партиции топика
        topic = settings.KAFKA_TOPIC_EVENTS
        
        # Принудительно запрашиваем метаданные топика
        await consumer._client.force_metadata_update()
        await asyncio.sleep(0.5)

        topic_partitions = consumer.partitions_for_topic(topic)
        
        if not topic_partitions:
            logger.info("⚠️ No partitions found. Topic might be empty or not created yet.")
            return
            
        partitions = [TopicPartition(topic, p) for p in topic_partitions]
        consumer.assign(partitions)

        # Ищем конец лога (High Watermark - последние актуальные смещения)
        end_offsets = await consumer.end_offsets(partitions)

        # Проверяем, есть ли вообще сообщения в Kafka
        has_messages = any(offset > 0 for offset in end_offsets.values())
        if not has_messages:
            logger.info("📭 Kafka topic is empty. Nothing to replay.")
            return

        # Принудительно перемещаемся в самое начало лога
        await consumer.seek_to_beginning()

        events_processed = 0

        while True:
            # Проверяем, достигли ли мы конца лога по всем партициям
            reached_end = True
            for p in partitions:
                if await consumer.position(p) < end_offsets[p]:
                    reached_end = False
                    break

            if reached_end:
                break

            # Читаем батчами (ускоряет процесс)
            batch = await consumer.getmany(timeout_ms=2000, max_records=200)
            if not batch:
                break # Если ничего не пришло по таймауту — выходим

            async with AsyncSessionLocal() as db:
                for tp, messages in batch.items():
                    for msg in messages:
                        # Пропускаем события, которые не относятся к сессиям/сообщениям 
                        # (вдруг там есть события Characters или Personas)
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
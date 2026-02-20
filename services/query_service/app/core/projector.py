import json
import asyncio
import logging
import uuid
from datetime import datetime
from aiokafka import AIOKafkaConsumer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.base import AsyncSessionLocal
from app.models.read_models import SessionReadModel, MessageReadModel, CharacterReadModel, ScenarioReadModel, UserPersonaReadModel, LoreItemReadModel

logger = logging.getLogger("query_projector")

def to_uuid(val: str | None) -> uuid.UUID | None:
    if not val: return None
    return uuid.UUID(str(val))

def to_datetime(val: str | None) -> datetime | None:
    if not val: return None
    if isinstance(val, str):
        return datetime.fromisoformat(val.replace('Z', '+00:00'))
    return val

async def process_event(event_data: dict, db: AsyncSession):
    event_type = event_data.get("event_type")
    entity_type = event_data.get("entity_type")
    entity_id_str = event_data.get("entity_id")
    
    if not event_type or not entity_id_str:
        return

    entity_id = to_uuid(entity_id_str)

    # Session events
    if event_type == "SessionCreated":
        existing = await db.execute(select(SessionReadModel).where(SessionReadModel.id == entity_id))
        if existing.scalar_one_or_none():
            return # Уже спроецировано
            
        new_session = SessionReadModel(
            id=entity_id,
            user_id=to_uuid(event_data.get("user_id")),
            character_id=to_uuid(event_data.get("character_id")),
            persona_id=to_uuid(event_data.get("persona_id")),
            scenario_id=to_uuid(event_data.get("scenario_id")),
            mode=event_data.get("mode"),
            language=event_data.get("language"),
            speech_style=event_data.get("speech_style"),
            character_name_snapshot=event_data.get("character_name_snapshot"),
            persona_name_snapshot=event_data.get("persona_name_snapshot"),
            relationship_context=event_data.get("relationship_context"),
            current_step=0,
            created_at=to_datetime(event_data.get("timestamp"))
        )
        db.add(new_session)
        await db.commit()
        logger.info(f"[Query Projector] Session {entity_id} saved to Read Model.")

    elif event_type == "MessageAdded":
        existing = await db.execute(select(MessageReadModel).where(MessageReadModel.id == entity_id))
        if existing.scalar_one_or_none():
            return
            
        new_msg = MessageReadModel(
            id=entity_id,
            session_id=to_uuid(event_data.get("session_id")),
            parent_id=to_uuid(event_data.get("parent_id")),
            role=event_data.get("role"),
            content=event_data.get("content"),
            is_active=True,
            created_at=to_datetime(event_data.get("timestamp"))
        )
        db.add(new_msg)
        
        # Обновляем время активности сессии
        session = await db.get(SessionReadModel, to_uuid(event_data.get("session_id")))
        if session:
            session.updated_at = to_datetime(event_data.get("timestamp"))
            db.add(session)
            
        await db.commit()
        logger.info(f"[Query Projector] Message {entity_id} saved to Read Model.")

    # Character events
    elif entity_type == "Character":
        if event_type == "Created":
            payload = event_data.get("payload", {})
            char = CharacterReadModel(
                id=entity_id,
                name=payload.get("name", ""),
                avatar_url=payload.get("avatar_url"),
                appearance=payload.get("appearance", ""),
                personality_traits=payload.get("personality_traits", ""),
                dialogue_style=payload.get("dialogue_style", ""),
                inner_world=payload.get("inner_world"),
                behavioral_cues=payload.get("behavioral_cues")
            )
            db.add(char)
            await db.commit()
            logger.info(f"[Query Projector] Character {entity_id} created.")

    # Scenario events
    elif entity_type == "Scenario":
        if event_type == "Created":
            payload = event_data.get("payload", {})
            scenario = ScenarioReadModel(
                id=entity_id,
                owner_character_id=to_uuid(payload.get("character_id")),
                title=payload.get("title", ""),
                description=payload.get("description", ""),
                start_point=payload.get("start_point", ""),
                end_point=payload.get("end_point", ""),
                suggested_relationships=payload.get("suggested_relationships", [])
            )
            db.add(scenario)
            await db.commit()
            logger.info(f"[Query Projector] Scenario {entity_id} created.")

    # Persona events
    elif entity_type == "Persona":
        if event_type == "Created":
            payload = event_data.get("payload", {})
            persona = UserPersonaReadModel(
                id=entity_id,
                owner_id=to_uuid(payload.get("owner_id")),
                name=payload.get("name", ""),
                description=payload.get("description", ""),
                avatar_url=payload.get("avatar_url"),
                created_at=to_datetime(event_data.get("timestamp"))
            )
            db.add(persona)
            await db.commit()
            logger.info(f"[Query Projector] Persona {entity_id} created.")

    # LoreItem events
    elif entity_type == "LoreItem":
        if event_type == "Created":
            payload = event_data.get("payload", {})
            lore = LoreItemReadModel(
                id=entity_id,
                character_id=to_uuid(payload.get("character_id")),
                category=payload.get("category", "fact"),
                content=payload.get("content", ""),
                keywords=payload.get("keywords")
            )
            db.add(lore)
            await db.commit()
            logger.info(f"[Query Projector] LoreItem {entity_id} created.")

    # TODO: Добавить Updated/Deleted для всех сущностей

async def consume_events_forever():
    """Фоновая задача для прослушивания Kafka"""
    consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC_EVENTS,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="query_service_read_model_projector", # <- Уникальный ID группы для Query!
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset="earliest"
    )
    
    while True:
        try:
            await consumer.start()
            logger.info("🎧 Query Read Model Projector successfully connected to Kafka!")
            break
        except Exception as e:
            logger.warning(f"⏳ Waiting for Kafka... ({e})")
            await asyncio.sleep(3)
            
    try:
        async for msg in consumer:
            event_data = msg.value
            try:
                async with AsyncSessionLocal() as db:
                    await process_event(event_data, db)
            except Exception as e:
                logger.error(f"Error processing event {event_data.get('event_id')}: {e}")
    except asyncio.CancelledError:
        logger.info("🛑 Projector task was cancelled.")
    finally:
        await consumer.stop()
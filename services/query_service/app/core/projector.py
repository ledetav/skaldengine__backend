import json
import asyncio
import logging
import uuid
from datetime import datetime
from aiokafka import AIOKafkaConsumer
from sqlalchemy import select, delete
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
    entity_type = event_data.get("entity_type") or event_data.get("aggregate_type")
    entity_id_str = event_data.get("entity_id") or event_data.get("aggregate_id")
    
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
        elif event_type == "Updated":
            char = await db.get(CharacterReadModel, entity_id)
            if char:
                payload = event_data.get("payload", {})
                if "name" in payload: char.name = payload["name"]
                if "avatar_url" in payload: char.avatar_url = payload["avatar_url"]
                if "appearance" in payload: char.appearance = payload["appearance"]
                if "personality_traits" in payload: char.personality_traits = payload["personality_traits"]
                if "dialogue_style" in payload: char.dialogue_style = payload["dialogue_style"]
                if "inner_world" in payload: char.inner_world = payload["inner_world"]
                if "behavioral_cues" in payload: char.behavioral_cues = payload["behavioral_cues"]
                await db.commit()
                logger.info(f"[Query Projector] Character {entity_id} updated.")
        elif event_type == "Deleted":
            await db.execute(delete(CharacterReadModel).where(CharacterReadModel.id == entity_id))
            await db.commit()
            logger.info(f"[Query Projector] Character {entity_id} deleted.")

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
        elif event_type == "Updated":
            scenario = await db.get(ScenarioReadModel, entity_id)
            if scenario:
                payload = event_data.get("payload", {})
                if "title" in payload: scenario.title = payload["title"]
                if "description" in payload: scenario.description = payload["description"]
                if "start_point" in payload: scenario.start_point = payload["start_point"]
                if "end_point" in payload: scenario.end_point = payload["end_point"]
                if "suggested_relationships" in payload: scenario.suggested_relationships = payload["suggested_relationships"]
                await db.commit()
                logger.info(f"[Query Projector] Scenario {entity_id} updated.")
        elif event_type == "Deleted":
            await db.execute(delete(ScenarioReadModel).where(ScenarioReadModel.id == entity_id))
            await db.commit()
            logger.info(f"[Query Projector] Scenario {entity_id} deleted.")

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
        elif event_type == "Updated":
            persona = await db.get(UserPersonaReadModel, entity_id)
            if persona:
                payload = event_data.get("payload", {})
                if "name" in payload: persona.name = payload["name"]
                if "description" in payload: persona.description = payload["description"]
                if "avatar_url" in payload: persona.avatar_url = payload["avatar_url"]
                await db.commit()
                logger.info(f"[Query Projector] Persona {entity_id} updated.")
        elif event_type == "Deleted":
            await db.execute(delete(UserPersonaReadModel).where(UserPersonaReadModel.id == entity_id))
            await db.commit()
            logger.info(f"[Query Projector] Persona {entity_id} deleted.")

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
        elif event_type == "Updated":
            lore = await db.get(LoreItemReadModel, entity_id)
            if lore:
                payload = event_data.get("payload", {})
                if "category" in payload: lore.category = payload["category"]
                if "content" in payload: lore.content = payload["content"]
                if "keywords" in payload: lore.keywords = payload["keywords"]
                await db.commit()
                logger.info(f"[Query Projector] LoreItem {entity_id} updated.")
        elif event_type == "Deleted":
            await db.execute(delete(LoreItemReadModel).where(LoreItemReadModel.id == entity_id))
            await db.commit()
            logger.info(f"[Query Projector] LoreItem {entity_id} deleted.")

    # Session lifecycle events
    elif event_type == "SessionDeleted":
        await db.execute(delete(MessageReadModel).where(MessageReadModel.session_id == entity_id))
        await db.execute(delete(SessionReadModel).where(SessionReadModel.id == entity_id))
        await db.commit()
        logger.info(f"[Query Projector] Session {entity_id} and its messages deleted.")

    # Message lifecycle events
    elif event_type == "MessageDeactivated":
        msg = await db.get(MessageReadModel, entity_id)
        if msg:
            msg.is_active = False
            await db.commit()
            logger.info(f"[Query Projector] Message {entity_id} deactivated.")

    # Saga: UserCoreDataPurged
    elif event_type == "UserCoreDataPurged":
        user_id = entity_id
        if user_id:
            sessions_query = await db.execute(select(SessionReadModel.id).where(SessionReadModel.user_id == user_id))
            session_ids = sessions_query.scalars().all()
            if session_ids:
                await db.execute(delete(MessageReadModel).where(MessageReadModel.session_id.in_(session_ids)))
            
            await db.execute(delete(SessionReadModel).where(SessionReadModel.user_id == user_id))
            await db.execute(delete(UserPersonaReadModel).where(UserPersonaReadModel.owner_id == user_id))
            
            await db.commit()
            logger.info(f"[Query Projector] Purged all read models for user {user_id}.")

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
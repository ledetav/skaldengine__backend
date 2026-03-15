from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from app.core.config import settings
from app.api.api import api_router
from app.core.kafka import get_kafka_producer, close_kafka_producer, outbox_relay_worker
from app.core.saga_consumer import consume_core_events_forever

outbox_task = None
saga_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global outbox_task, saga_task
    await get_kafka_producer()
    
    outbox_task = asyncio.create_task(outbox_relay_worker())
    saga_task = asyncio.create_task(consume_core_events_forever())
    
    yield
    
    if outbox_task:
        outbox_task.cancel()
        try: await outbox_task
        except asyncio.CancelledError: pass

    if saga_task:
        saga_task.cancel()
        try: await saga_task
        except asyncio.CancelledError: pass
            
    await close_kafka_producer()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    lifespan=lifespan
)
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "auth-service"}

@app.get("/")
def health_check():
    return {"status": "ok", "service": "auth-service"}
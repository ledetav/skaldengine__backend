import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.api import api_router
from app.core.kafka import get_kafka_producer, close_kafka_producer
from app.core.projector import consume_events_forever

projector_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global projector_task
    await get_kafka_producer()

    projector_task = asyncio.create_task(consume_events_forever())
    
    yield
    
    if projector_task:
        projector_task.cancel()
        try:
            await projector_task
        except asyncio.CancelledError:
            pass
            
    await close_kafka_producer()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Раздача статики (картинок)
app.mount("/static", StaticFiles(directory=settings.UPLOAD_DIR), name="static")

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "core-service"}
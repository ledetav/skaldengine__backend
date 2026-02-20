import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.projector import consume_events_forever

projector_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global projector_task
    # Запускаем консьюмер событий в фоне при старте сервиса
    projector_task = asyncio.create_task(consume_events_forever())
    
    yield
    
    # Корректно завершаем при остановке
    if projector_task:
        projector_task.cancel()
        try:
            await projector_task
        except asyncio.CancelledError:
            pass

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
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "query-service"}

# Позже здесь мы подключим роутеры для /sessions
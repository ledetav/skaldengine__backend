from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"], # Query сервис разрешает только GET запросы
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "query-service"}

# Позже подключить роутеры для /sessions
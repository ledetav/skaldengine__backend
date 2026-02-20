from fastapi import APIRouter
from app.api.endpoints import sessions, characters, scenarios, personas, lore

api_router = APIRouter()
api_router.include_router(sessions.router, prefix="/sessions", tags=["Read Sessions"])
api_router.include_router(characters.router, prefix="/characters", tags=["Read Characters"])
api_router.include_router(scenarios.router, prefix="/scenarios", tags=["Read Scenarios"])
api_router.include_router(personas.router, prefix="/personas", tags=["Read Personas"])
api_router.include_router(lore.router, prefix="/lore", tags=["Read Lore"])
from fastapi import APIRouter
from app.api.endpoints import user_personas, characters, lore, sessions, upload

api_router = APIRouter()

api_router.include_router(user_personas.router, prefix="/personas", tags=["User Personas"])
api_router.include_router(characters.router, prefix="/characters", tags=["AI Characters"])
api_router.include_router(lore.router, prefix="/lore", tags=["Characters Lore"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["Roleplay Sessions"])
api_router.include_router(upload.router, prefix="/upload", tags=["Files"])
from fastapi import APIRouter
from app.api.endpoints import (
    user_personas,
    characters,
    chats,
    lorebooks,
    scenarios,
    upload,
)

api_router = APIRouter()

api_router.include_router(user_personas.router, prefix="/personas",    tags=["User Personas"])
api_router.include_router(characters.router,    prefix="/characters",  tags=["AI Characters"])
api_router.include_router(chats.router,         prefix="/chats",       tags=["Chats & Messages"])
api_router.include_router(lorebooks.router,     prefix="/lorebooks",   tags=["Lorebooks"])
api_router.include_router(scenarios.router,     prefix="/scenarios",   tags=["Scenarios"])
api_router.include_router(upload.router,        prefix="/upload",      tags=["Files"])
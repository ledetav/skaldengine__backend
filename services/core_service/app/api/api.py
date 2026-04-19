from fastapi import APIRouter
from app.domains.persona import router as user_personas
from app.domains.character import router as characters
from app.domains.chat import router as chats
from app.domains.lorebook import router as lorebooks
from app.domains.scenario import router as scenarios
from app.domains.chat import message_router as messages
from app.domains.character import admin_router as admin_characters
from app.domains.character import attribute_router as admin_attributes
from app.domains.lorebook import admin_router as admin_lorebooks

# Temporary/Shared endpoints
from app.api.endpoints import upload, ws

api_router = APIRouter()

api_router.include_router(user_personas.router, prefix="/personas",    tags=["User Personas"])
api_router.include_router(characters.router,    prefix="/characters",  tags=["AI Characters"])
api_router.include_router(chats.router,         prefix="/chats",       tags=["Chats & Messages"])
api_router.include_router(lorebooks.router,     prefix="/lorebooks",   tags=["Lorebooks"])
api_router.include_router(scenarios.router,     prefix="/scenarios",   tags=["Scenarios"])
api_router.include_router(upload.router,        prefix="/upload",      tags=["Files"])
api_router.include_router(messages.router,      prefix="/messages",    tags=["Messages"])
api_router.include_router(ws.router,            prefix="/ws",          tags=["Real-time Updates"])

# Admin Endpoints (Require valid JWT with admin/moderator role)
api_router.include_router(admin_characters.router, prefix="/admin/characters", tags=["Admin Characters"])
api_router.include_router(admin_attributes.router, prefix="/admin/attributes", tags=["Admin Attributes"])
api_router.include_router(admin_lorebooks.router, prefix="/admin/lorebooks",   tags=["Admin Lorebooks"])

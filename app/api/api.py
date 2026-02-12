from fastapi import APIRouter
from app.api.endpoints import user_personas, auth, users, upload, characters, lore

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(user_personas.router, prefix="/personas", tags=["User Personas"])
api_router.include_router(upload.router, prefix="/upload", tags=["Files"])
api_router.include_router(characters.router, prefix="/characters", tags=["AI Characters"])
api_router.include_router(lore.router, prefix="/lore", tags=["Characters Lore"])
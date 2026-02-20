from fastapi import APIRouter
from app.api.endpoints import sessions

api_router = APIRouter()
api_router.include_router(sessions.router, prefix="/sessions", tags=["Read Sessions"])
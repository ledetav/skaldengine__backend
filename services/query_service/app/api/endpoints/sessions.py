from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api import deps
from app.models.read_models import SessionReadModel, MessageReadModel
from app.schemas.read_schemas import SessionRead, MessageRead

router = APIRouter()

@router.get("/", response_model=List[SessionRead])
async def get_user_sessions(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Получить список всех сессий текущего пользователя."""
    query = select(SessionReadModel)\
        .where(SessionReadModel.user_id == current_user.id)\
        .order_by(SessionReadModel.updated_at.desc())\
        .offset(skip)\
        .limit(limit)
        
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{session_id}", response_model=SessionRead)
async def get_session_details(
    session_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Получить детали конкретной сессии."""
    session = await db.get(SessionReadModel, session_id)
    if not session or str(session.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.get("/{session_id}/messages", response_model=List[MessageRead])
async def get_session_messages(
    session_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Получить историю сообщений сессии (только активные сообщения ветки)."""
    # Сначала проверяем права на сессию
    session = await db.get(SessionReadModel, session_id)
    if not session or str(session.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Выдаем сообщения
    query = select(MessageReadModel)\
        .where(MessageReadModel.session_id == session_id)\
        .where(MessageReadModel.is_active == True)\
        .order_by(MessageReadModel.created_at.asc())\
        .offset(skip)\
        .limit(limit)
        
    result = await db.execute(query)
    return result.scalars().all()
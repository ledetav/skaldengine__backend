from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.schemas.user import UserResponse
from app.models.user import User
from app.models.outbox import OutboxEvent

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def read_user_me(
    current_user: User = Depends(deps.get_current_user),
):
    """Получить текущего пользователя по токену"""
    return current_user

@router.delete("/me", status_code=status.HTTP_202_ACCEPTED)
async def delete_user_me(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Запрос на удаление аккаунта (Инициация Saga).
    Не удаляем юзера сразу, а переводим в статус deleting и отправляем ивент.
    """
    if current_user.status == "deleting":
        raise HTTPException(status_code=400, detail="Deletion already in progress")

    # 1. Меняем статус
    current_user.status = "deleting"
    db.add(current_user)

    outbox_event = OutboxEvent(
        aggregate_type="User",
        aggregate_id=str(current_user.id),
        event_type="UserDeletionRequested",
        payload={"email": current_user.email}
    )
    db.add(outbox_event)

    await db.commit()

    return {"message": "Account deletion requested. This process may take a few moments."}
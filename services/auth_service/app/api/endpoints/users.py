from fastapi import APIRouter, Depends
from app.api import deps
from app.schemas.user import UserResponse
from app.models.user import User

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def read_user_me(
    current_user: User = Depends(deps.get_current_user),
):
    """Получить текущего пользователя по токену"""
    return current_user
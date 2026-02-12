from fastapi import APIRouter, Depends
from app.api import deps
from app.schemas.user import User as UserSchema
from app.models.user import User

router = APIRouter()

@router.get("/me", response_model=UserSchema)
async def read_user_me(
    current_user: User = Depends(deps.get_current_user),
):
    return current_user
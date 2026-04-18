from typing import Any
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api import deps
from .auth_controller import AuthController
from app.domains.user.schemas import UserCreate
from shared.schemas.response import BaseResponse

router = APIRouter()

@router.post("/login", response_model=BaseResponse)
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    controller: AuthController = Depends(deps.get_auth_controller)
) -> Any:
    """
    OAuth2 compatible token login, retrieve an access token for future requests.
    """
    return await controller.login(form_data)

@router.post("/register", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    controller: AuthController = Depends(deps.get_auth_controller)
) -> Any:
    """
    Create a new user.
    """
    return await controller.register(user_in)
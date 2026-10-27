"""Роутер конечных точек аутентификации и регистрации."""

import traceback
from typing import Any
from fastapi import APIRouter, Depends, status, Body
from fastapi.security import OAuth2PasswordRequestForm

from app.api import deps
from .auth_controller import AuthController
from app.domains.user.schemas import UserCreate, UserLogin
from shared.schemas.response import BaseResponse

router = APIRouter()


@router.post("/login", response_model=BaseResponse)
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    controller: AuthController = Depends(deps.get_auth_controller)
) -> Any:
    """OAuth2-совместимый вход по логину и паролю (form-data: username + password)."""
    return await controller.login(form_data)


@router.post("/login/json", response_model=BaseResponse)
async def login_json(
    body: UserLogin,
    controller: AuthController = Depends(deps.get_auth_controller)
) -> Any:
    """Вход с передачей JSON в теле запроса (логин + пароль) для веб-клиента."""
    from fastapi.security import OAuth2PasswordRequestForm as _Form

    class _FakeForm:
        """Адаптер формы аутентификации, имитирующий структуру OAuth2PasswordRequestForm."""
        username = body.login
        password = body.password

    return await controller.login(_FakeForm())


@router.post("/register", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    controller: AuthController = Depends(deps.get_auth_controller)
) -> Any:
    """Регистрация нового пользователя."""
    try:
        result = await controller.register(user_in)
        return result
    except Exception as e:
        logger_error_trace = traceback.format_exc()
        print(f"\nОшибка при регистрации пользователя: {e}\n{logger_error_trace}")
        raise e


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
    """
    OAuth2 compatible token login (form-data: username + password).
    """
    return await controller.login(form_data)


@router.post("/login/json", response_model=BaseResponse)
async def login_json(
    body: UserLogin,
    controller: AuthController = Depends(deps.get_auth_controller)
) -> Any:
    """
    JSON-body login (identifier + password). For use by the frontend.
    """
    from fastapi.security import OAuth2PasswordRequestForm as _Form

    class _FakeForm:
        username = body.login
        password = body.password

    return await controller.login(_FakeForm())


@router.post("/register", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    controller: AuthController = Depends(deps.get_auth_controller)
) -> Any:
    """
    Create a new user.
    """
    try:
        print("\n--- НАЧИНАЕМ РЕГИСТРАЦИЮ ---")
        
        # Вот тут вызывается код, который падает
        result = await controller.register(user_in)
        
        print("--- РЕГИСТРАЦИЯ УСПЕШНА, РЕЗУЛЬТАТ:", result)
        return result
        
    except Exception as e:
        # ВОТ ЭТО МЫ ТОЧНО УВИДИМ В КОНСОЛИ!
        print("\n!!! ПОЙМАЛИ ОШИБКУ В РОУТЕРЕ !!!")
        traceback.print_exc()
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
        raise e

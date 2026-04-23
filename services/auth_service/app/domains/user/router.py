from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt, JWTError

from app.api import deps
from .controller import UserController
from app.domains.user.models import User
from app.domains.user.schemas import UserResponse, LoginUpdate, UsernameUpdate, EmailUpdate, PasswordUpdate, FullNameUpdate, ProfileUpdate, UserUpdate
from shared.schemas.response import BaseResponse
from app.core.config import settings
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()

_http_bearer = HTTPBearer()

async def _verify_staff_from_token(
    token_auth: HTTPAuthorizationCredentials = Depends(_http_bearer),
) -> None:
    """Check that the JWT token belongs to an admin or moderator."""
    try:
        payload = jwt.decode(
            token_auth.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        role = payload.get("role", "user")
    except (JWTError, ValueError):
        raise HTTPException(status_code=403, detail="Could not validate credentials")
    if role not in ("admin", "moderator"):
        raise HTTPException(status_code=403, detail="Not enough privileges")

@router.get("/", response_model=BaseResponse, dependencies=[Depends(_verify_staff_from_token)])
async def list_all_users(
    skip: int = 0,
    limit: int = 200,
    controller: UserController = Depends(deps.get_user_controller),
):
    """Получить список всех пользователей (только для admin/moderator)."""
    return await controller.get_all_users(skip=skip, limit=limit)


@router.get("/me", response_model=BaseResponse)
async def read_user_me(
    current_user: User = Depends(deps.get_current_user),
):
    """Получить информацию о текущем пользователе по токену."""
    return BaseResponse(success=True, data=UserResponse.model_validate(current_user))

@router.get("/profile/{username}", response_model=BaseResponse)
async def read_public_profile(
    username: str,
    controller: UserController = Depends(deps.get_user_controller)
):
    """Получить публичный профиль пользователя по его username."""
    if username.startswith("@"):
        username = username[1:]
    return await controller.get_public_profile(username)


@router.get("/me/login", response_model=BaseResponse)
async def get_my_login(
    current_user: User = Depends(deps.get_current_user),
):
    """Вернуть только логин текущего пользователя."""
    return BaseResponse(success=True, data={"login": current_user.login})


@router.get("/me/username", response_model=BaseResponse)
async def get_my_username(
    current_user: User = Depends(deps.get_current_user),
):
    """Вернуть только юзернейм (handle) текущего пользователя."""
    return BaseResponse(success=True, data={"username": current_user.username})


@router.patch("/me/login", response_model=BaseResponse)
async def update_login(
    update_in: LoginUpdate,
    current_user: User = Depends(deps.get_current_user),
    controller: UserController = Depends(deps.get_user_controller)
):
    """Изменить логин пользователя."""
    return await controller.update_login(current_user, update_in)


@router.patch("/me/username", response_model=BaseResponse)
async def update_username(
    update_in: UsernameUpdate,
    current_user: User = Depends(deps.get_current_user),
    controller: UserController = Depends(deps.get_user_controller)
):
    """Изменить публичный юзернейм (handle) пользователя."""
    return await controller.update_username(current_user, update_in)


@router.patch("/me/full-name", response_model=BaseResponse)
async def update_full_name(
    update_in: FullNameUpdate,
    current_user: User = Depends(deps.get_current_user),
    controller: UserController = Depends(deps.get_user_controller)
):
    """Изменить имя пользователя."""
    return await controller.update_full_name(current_user, update_in)


@router.patch("/me/email", response_model=BaseResponse)
async def update_email(
    update_in: EmailUpdate,
    current_user: User = Depends(deps.get_current_user),
    controller: UserController = Depends(deps.get_user_controller)
):
    """Изменить почту пользователя."""
    return await controller.update_email(current_user, update_in)


    """Изменить пароль пользователя."""
    return await controller.update_password(current_user, update_in)


@router.patch("/me/profile", response_model=BaseResponse)
async def update_profile(
    update_in: ProfileUpdate,
    current_user: User = Depends(deps.get_current_user),
    controller: UserController = Depends(deps.get_user_controller)
):
    """Обновить аватар или обложку профиля."""
    return await controller.update_profile(current_user, update_in)


@router.patch("/me", response_model=BaseResponse)
async def update_user_me(
    update_in: UserUpdate,
    current_user: User = Depends(deps.get_current_user),
    controller: UserController = Depends(deps.get_user_controller)
):
    """Обновить данные профиля пользователя (универсальный метод)."""
    return await controller.update_me(current_user, update_in)


@router.delete("/me", response_model=BaseResponse, status_code=status.HTTP_200_OK)
async def delete_user(
    current_user: User = Depends(deps.get_current_user),
    controller: UserController = Depends(deps.get_user_controller)
):
    """Удалить учетную запись текущего пользователя."""
    return await controller.delete_user(current_user)
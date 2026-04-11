from typing import Any
from fastapi import APIRouter, Depends, status

from app.api import deps
from .controller import UserController
from app.models.user import User
from app.schemas.user import UserResponse, LoginUpdate, UsernameUpdate, EmailUpdate, PasswordUpdate, FullNameUpdate, ProfileUpdate, UserUpdate
from app.schemas.response import BaseResponse

router = APIRouter()

@router.get("/me", response_model=BaseResponse)
async def read_user_me(
    current_user: User = Depends(deps.get_current_user),
):
    """Получить информацию о текущем пользователе по токену."""
    return BaseResponse(success=True, data=current_user)

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
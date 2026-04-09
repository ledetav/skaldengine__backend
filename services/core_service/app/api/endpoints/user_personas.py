from uuid import UUID
from fastapi import APIRouter, Depends, status

from app.api import deps
from app.api.controllers.user_persona_controller import UserPersonaController
from app.schemas.response import BaseResponse
from app.schemas.user_persona import UserPersonaCreate, UserPersonaUpdate

router = APIRouter()

@router.get("/", response_model=BaseResponse)
async def list_my_personas(
    controller: UserPersonaController = Depends(deps.get_user_persona_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Получить список всех персон текущего пользователя."""
    return await controller.get_my_personas(current_user.id)

@router.get("/stats", response_model=BaseResponse)
async def get_my_stats(
    current_user: deps.CurrentUser = Depends(deps.get_current_user),
    controller: UserPersonaController = Depends(deps.get_user_persona_controller)
):
    """Получить агрегированную статистику пользователя (чаты, персоны, лорбуки)."""
    return await controller.get_user_stats(current_user.id)


@router.post("/", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_persona(
    persona_in: UserPersonaCreate,
    controller: UserPersonaController = Depends(deps.get_user_persona_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Создать новую игровую персону."""
    return await controller.create_persona(persona_in, current_user.id)


@router.get("/{persona_id}", response_model=BaseResponse)
async def read_persona(
    persona_id: UUID,
    controller: UserPersonaController = Depends(deps.get_user_persona_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Получить детали конкретной персоны."""
    return await controller.get_persona(persona_id, current_user.id)


@router.patch("/{persona_id}", response_model=BaseResponse)
async def update_persona(
    persona_id: UUID,
    persona_in: UserPersonaUpdate,
    controller: UserPersonaController = Depends(deps.get_user_persona_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Обновить данные персоны."""
    return await controller.update_persona(persona_id, persona_in, current_user.id)


@router.delete("/{persona_id}", response_model=BaseResponse, status_code=status.HTTP_200_OK)
async def delete_persona(
    persona_id: UUID,
    controller: UserPersonaController = Depends(deps.get_user_persona_controller),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Удалить персону."""
    return await controller.delete_persona(persona_id, current_user.id)
from uuid import UUID
from fastapi import APIRouter, Depends, status

from app.api import deps
from .controller import UserPersonaController
from .schemas import UserPersonaCreate, UserPersonaUpdate, UserPersona
from shared.schemas.response import BaseResponse

router = APIRouter()

@router.get("/admin/all", response_model=BaseResponse)
async def list_all_personas(
    skip: int = 0,
    limit: int = 200,
    controller: UserPersonaController = Depends(deps.get_user_persona_controller),
    current_user: deps.CurrentUser = Depends(deps.verify_staff_role)
):
    """[Admin/Moderator] Получить список всех персон всех пользователей."""
    personas = await controller.persona_service.repository.get_multi(skip=skip, limit=limit)
    return BaseResponse(success=True, data=personas)


@router.delete("/admin/{persona_id}", response_model=BaseResponse, status_code=status.HTTP_200_OK)
async def delete_persona_admin(
    persona_id: UUID,
    controller: UserPersonaController = Depends(deps.get_user_persona_controller),
    current_user: deps.CurrentUser = Depends(deps.verify_admin_role)
):
    """[Admin] Удалить любую персону."""
    return await controller.delete_persona(persona_id, current_user.id, is_admin=True)


@router.get("/", response_model=BaseResponse)
async def list_personas(
    user_id: UUID | None = None,
    controller: UserPersonaController = Depends(deps.get_user_persona_controller),
    current_user: deps.CurrentUser | None = Depends(deps.get_optional_current_user)
):
    """Получить список всех персон (своих или указанного пользователя)."""
    target_id = user_id or (current_user.id if current_user else None)
    if not target_id:
        return BaseResponse(success=False, message="User ID required")
    return await controller.get_my_personas(target_id)

@router.get("/stats", response_model=BaseResponse)
async def get_user_stats(
    user_id: UUID | None = None,
    current_user: deps.CurrentUser | None = Depends(deps.get_optional_current_user),
    controller: UserPersonaController = Depends(deps.get_user_persona_controller)
):
    """Получить агрегированную статистику пользователя (чаты, персоны, лорбуки)."""
    target_id = user_id or (current_user.id if current_user else None)
    if not target_id:
        return BaseResponse(success=False, message="User ID required")
    return await controller.get_user_stats(target_id)


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
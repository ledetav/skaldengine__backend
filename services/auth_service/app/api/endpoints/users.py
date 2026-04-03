from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api import deps
from app.core import security
from app.schemas.user import UserResponse, UsernameUpdate, EmailUpdate, PasswordUpdate
from app.models.user import User

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def read_user_me(
    current_user: User = Depends(deps.get_current_user),
):
    """Получить информацию о текущем пользователе по токену."""
    return current_user


@router.get("/me/username")
async def get_my_username(
    current_user: User = Depends(deps.get_current_user),
):
    """Вернуть только юзернейм текущего пользователя."""
    return {"username": current_user.username}


@router.patch("/me/username", response_model=UserResponse)
async def update_username(
    update_in: UsernameUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Изменить юзернейм пользователя."""
    # Проверка на уникальность
    query = select(User).where(User.username == update_in.new_username)
    result = await db.execute(query)
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already taken")
    
    current_user.username = update_in.new_username
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.patch("/me/email", response_model=UserResponse)
async def update_email(
    update_in: EmailUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Изменить почту пользователя."""
    # Проверка на уникальность
    query = select(User).where(User.email == update_in.new_email)
    result = await db.execute(query)
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    current_user.email = update_in.new_email
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.post("/me/password")
async def update_password(
    update_in: PasswordUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Изменить пароль пользователя."""
    if not security.verify_password(update_in.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect old password")
    
    current_user.password_hash = security.get_password_hash(update_in.new_password)
    db.add(current_user)
    await db.commit()
    return {"message": "Password updated successfully"}


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Удалить учетную запись текущего пользователя."""
    await db.delete(current_user)
    await db.commit()
    return None
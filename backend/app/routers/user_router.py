"""User management endpoints (admin only for writes)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_active_user, require_admin
from app.dependencies.pagination import pagination_params
from app.models.user import User
from app.schemas.common import Message, Page, PageParams
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=201, dependencies=[Depends(require_admin)])
def create_user(
    payload: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)
) -> UserRead:
    return UserService(db).create(payload, actor_id=current_user.id)


@router.get("", response_model=Page[UserRead])
def list_users(
    db: Session = Depends(get_db),
    params: PageParams = Depends(pagination_params),
    email: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    _: User = Depends(get_current_active_user),
) -> Page[UserRead]:
    return UserService(db).list(params, filters={"email": email, "is_active": is_active})


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_active_user)
) -> UserRead:
    return UserService(db).get(user_id)


@router.patch("/{user_id}", response_model=UserRead, dependencies=[Depends(require_admin)])
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> UserRead:
    return UserService(db).update(user_id, payload, actor_id=current_user.id)


@router.delete("/{user_id}", response_model=Message, dependencies=[Depends(require_admin)])
def delete_user(
    user_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_admin)
) -> Message:
    UserService(db).soft_delete(user_id, actor_id=current_user.id)
    return Message(detail="User deleted")

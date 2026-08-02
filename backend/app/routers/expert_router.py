"""Expert profile endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_active_user, require_admin
from app.dependencies.pagination import pagination_params
from app.models.user import User
from app.schemas.common import Message, Page, PageParams
from app.schemas.expert import ExpertCreate, ExpertRead, ExpertUpdate
from app.services.expert_service import ExpertService

router = APIRouter(prefix="/experts", tags=["experts"])


@router.post("", response_model=ExpertRead, status_code=201, dependencies=[Depends(require_admin)])
def create_expert(
    payload: ExpertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> ExpertRead:
    return ExpertService(db).create(payload, actor_id=current_user.id)


@router.get("", response_model=Page[ExpertRead])
def list_experts(
    db: Session = Depends(get_db),
    params: PageParams = Depends(pagination_params),
    specialty: str | None = Query(default=None),
    _: User = Depends(get_current_active_user),
) -> Page[ExpertRead]:
    return ExpertService(db).list(params, filters={"specialty": specialty})


@router.get("/{expert_id}", response_model=ExpertRead)
def get_expert(
    expert_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_active_user)
) -> ExpertRead:
    return ExpertService(db).get(expert_id)


@router.patch("/{expert_id}", response_model=ExpertRead, dependencies=[Depends(require_admin)])
def update_expert(
    expert_id: uuid.UUID,
    payload: ExpertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> ExpertRead:
    return ExpertService(db).update(expert_id, payload, actor_id=current_user.id)


@router.delete("/{expert_id}", response_model=Message, dependencies=[Depends(require_admin)])
def delete_expert(
    expert_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_admin)
) -> Message:
    ExpertService(db).soft_delete(expert_id, actor_id=current_user.id)
    return Message(detail="Expert deleted")

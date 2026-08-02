"""Decision domain endpoints (Used Car Purchase, Real Estate, ...)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_active_user, require_admin
from app.dependencies.pagination import pagination_params
from app.models.user import User
from app.schemas.common import Message, Page, PageParams
from app.schemas.domain import DomainCreate, DomainRead, DomainUpdate
from app.services.domain_service import DomainService

router = APIRouter(prefix="/domains", tags=["domains"])


@router.post("", response_model=DomainRead, status_code=201, dependencies=[Depends(require_admin)])
def create_domain(
    payload: DomainCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> DomainRead:
    return DomainService(db).create(payload, actor_id=current_user.id)


@router.get("", response_model=Page[DomainRead])
def list_domains(
    db: Session = Depends(get_db),
    params: PageParams = Depends(pagination_params),
    code: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    _: User = Depends(get_current_active_user),
) -> Page[DomainRead]:
    return DomainService(db).list(params, filters={"code": code, "is_active": is_active})


@router.get("/{domain_id}", response_model=DomainRead)
def get_domain(
    domain_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_active_user)
) -> DomainRead:
    return DomainService(db).get(domain_id)


@router.patch("/{domain_id}", response_model=DomainRead, dependencies=[Depends(require_admin)])
def update_domain(
    domain_id: uuid.UUID,
    payload: DomainUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> DomainRead:
    return DomainService(db).update(domain_id, payload, actor_id=current_user.id)


@router.delete("/{domain_id}", response_model=Message, dependencies=[Depends(require_admin)])
def delete_domain(
    domain_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_admin)
) -> Message:
    DomainService(db).soft_delete(domain_id, actor_id=current_user.id)
    return Message(detail="Domain deleted")

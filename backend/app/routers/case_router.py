"""Case endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.constants import CaseStatus
from app.database.session import get_db
from app.dependencies.auth import get_current_active_user
from app.dependencies.pagination import pagination_params
from app.models.user import User
from app.schemas.case import CaseCreate, CaseRead, CaseUpdate
from app.schemas.common import Message, Page, PageParams
from app.services.case_service import CaseService

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("", response_model=CaseRead, status_code=201)
def create_case(
    payload: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CaseRead:
    return CaseService(db).create(payload, owner_id=current_user.id)


@router.get("", response_model=Page[CaseRead])
def list_cases(
    db: Session = Depends(get_db),
    params: PageParams = Depends(pagination_params),
    domain_id: uuid.UUID | None = Query(default=None),
    status_filter: CaseStatus | None = Query(default=None, alias="status"),
    owner_id: uuid.UUID | None = Query(default=None),
    _: User = Depends(get_current_active_user),
) -> Page[CaseRead]:
    return CaseService(db).list(
        params, filters={"domain_id": domain_id, "status": status_filter, "owner_id": owner_id}
    )


@router.get("/{case_id}", response_model=CaseRead)
def get_case(
    case_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_active_user)
) -> CaseRead:
    return CaseService(db).get(case_id)


@router.patch("/{case_id}", response_model=CaseRead)
def update_case(
    case_id: uuid.UUID,
    payload: CaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CaseRead:
    return CaseService(db).update(case_id, payload, actor_id=current_user.id)


@router.delete("/{case_id}", response_model=Message)
def delete_case(
    case_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Message:
    CaseService(db).soft_delete(case_id, actor_id=current_user.id)
    return Message(detail="Case deleted")

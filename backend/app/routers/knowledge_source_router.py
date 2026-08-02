"""KnowledgeSource endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_active_user, require_expert
from app.dependencies.pagination import pagination_params
from app.models.user import User
from app.schemas.common import Message, Page, PageParams
from app.schemas.evidence import KnowledgeSourceCreate, KnowledgeSourceRead, KnowledgeSourceUpdate
from app.services.response_service import KnowledgeSourceService

router = APIRouter(prefix="/knowledge-sources", tags=["knowledge-sources"])


@router.post(
    "", response_model=KnowledgeSourceRead, status_code=201, dependencies=[Depends(require_expert)]
)
def create_source(
    payload: KnowledgeSourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_expert),
) -> KnowledgeSourceRead:
    return KnowledgeSourceService(db).create(payload, actor_id=current_user.id)


@router.get("", response_model=Page[KnowledgeSourceRead])
def list_sources(
    db: Session = Depends(get_db),
    params: PageParams = Depends(pagination_params),
    name: str | None = Query(default=None),
    source_type: str | None = Query(default=None),
    _: User = Depends(get_current_active_user),
) -> Page[KnowledgeSourceRead]:
    return KnowledgeSourceService(db).list(
        params, filters={"name": name, "source_type": source_type}
    )


@router.get("/{source_id}", response_model=KnowledgeSourceRead)
def get_source(
    source_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_active_user)
) -> KnowledgeSourceRead:
    return KnowledgeSourceService(db).get(source_id)


@router.patch(
    "/{source_id}", response_model=KnowledgeSourceRead, dependencies=[Depends(require_expert)]
)
def update_source(
    source_id: uuid.UUID,
    payload: KnowledgeSourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_expert),
) -> KnowledgeSourceRead:
    return KnowledgeSourceService(db).update(source_id, payload, actor_id=current_user.id)


@router.delete("/{source_id}", response_model=Message, dependencies=[Depends(require_expert)])
def delete_source(
    source_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_expert),
) -> Message:
    KnowledgeSourceService(db).soft_delete(source_id, actor_id=current_user.id)
    return Message(detail="Knowledge source deleted")

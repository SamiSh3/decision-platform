"""Attachment metadata endpoints (polymorphic - any entity_type/entity_id)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_active_user
from app.dependencies.pagination import pagination_params
from app.models.user import User
from app.schemas.attachment import AttachmentCreate, AttachmentRead
from app.schemas.common import Message, Page, PageParams
from app.services.attachment_service import AttachmentService

router = APIRouter(prefix="/attachments", tags=["attachments"])


@router.post("", response_model=AttachmentRead, status_code=201)
def create_attachment(
    payload: AttachmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AttachmentRead:
    return AttachmentService(db).create(payload, actor_id=current_user.id)


@router.get("", response_model=Page[AttachmentRead])
def list_attachments(
    db: Session = Depends(get_db),
    params: PageParams = Depends(pagination_params),
    entity_type: str | None = Query(default=None),
    _: User = Depends(get_current_active_user),
) -> Page[AttachmentRead]:
    return AttachmentService(db).list(params, filters={"entity_type": entity_type})


@router.get("/by-entity/{entity_type}/{entity_id}", response_model=list[AttachmentRead])
def list_for_entity(
    entity_type: str,
    entity_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[AttachmentRead]:
    return AttachmentService(db).list_for_entity(entity_type, entity_id)


@router.get("/{attachment_id}", response_model=AttachmentRead)
def get_attachment(
    attachment_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> AttachmentRead:
    return AttachmentService(db).get(attachment_id)


@router.delete("/{attachment_id}", response_model=Message)
def delete_attachment(
    attachment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Message:
    AttachmentService(db).soft_delete(attachment_id, actor_id=current_user.id)
    return Message(detail="Attachment deleted")

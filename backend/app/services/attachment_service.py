"""Attachment service - metadata for uploaded files linked to any entity."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.repositories.audit_repository import AttachmentRepository
from app.schemas.attachment import AttachmentCreate, AttachmentRead
from app.schemas.common import Page, PageParams


class AttachmentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AttachmentRepository(db)

    def create(self, payload: AttachmentCreate, actor_id: uuid.UUID | None) -> AttachmentRead:
        instance = self.repo.create(payload.model_dump(), actor_id=actor_id)
        self.db.commit()
        return AttachmentRead.model_validate(instance)

    def get(self, entity_id: uuid.UUID) -> AttachmentRead:
        return AttachmentRead.model_validate(self.repo.get_or_404(entity_id))

    def list_for_entity(self, entity_type: str, entity_id: uuid.UUID) -> list[AttachmentRead]:
        items = self.repo.list_for_entity(entity_type, entity_id)
        return [AttachmentRead.model_validate(i) for i in items]

    def list(self, params: PageParams, filters: dict | None = None) -> Page[AttachmentRead]:
        items, total = self.repo.list(
            filters=filters,
            page=params.page,
            page_size=params.page_size,
            sort_by=params.sort_by,
            sort_dir=params.sort_dir,
        )
        return Page.create(
            [AttachmentRead.model_validate(i) for i in items], total, params.page, params.page_size
        )

    def soft_delete(self, entity_id: uuid.UUID, actor_id: uuid.UUID | None) -> None:
        instance = self.repo.get_or_404(entity_id)
        self.repo.soft_delete(instance, actor_id=actor_id)
        self.db.commit()

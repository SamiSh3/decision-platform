"""Domain service - manages decision domains (Used Car Purchase, Real Estate, ...)."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.domain_repository import DomainRepository
from app.schemas.common import Page, PageParams
from app.schemas.domain import DomainCreate, DomainRead, DomainUpdate


class DomainService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = DomainRepository(db)

    def create(self, payload: DomainCreate, actor_id: uuid.UUID | None) -> DomainRead:
        if self.repo.get_by_code(payload.code) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Domain code already exists"
            )
        instance = self.repo.create(payload.model_dump(), actor_id=actor_id)
        self.db.commit()
        return DomainRead.model_validate(instance)

    def get(self, entity_id: uuid.UUID) -> DomainRead:
        return DomainRead.model_validate(self.repo.get_or_404(entity_id))

    def list(self, params: PageParams, filters: dict | None = None) -> Page[DomainRead]:
        items, total = self.repo.list(
            filters=filters,
            page=params.page,
            page_size=params.page_size,
            sort_by=params.sort_by,
            sort_dir=params.sort_dir,
        )
        return Page.create(
            [DomainRead.model_validate(i) for i in items], total, params.page, params.page_size
        )

    def update(
        self, entity_id: uuid.UUID, payload: DomainUpdate, actor_id: uuid.UUID | None
    ) -> DomainRead:
        instance = self.repo.get_or_404(entity_id)
        instance = self.repo.update(
            instance, payload.model_dump(exclude_unset=True), actor_id=actor_id
        )
        self.db.commit()
        return DomainRead.model_validate(instance)

    def soft_delete(self, entity_id: uuid.UUID, actor_id: uuid.UUID | None) -> None:
        instance = self.repo.get_or_404(entity_id)
        self.repo.soft_delete(instance, actor_id=actor_id)
        self.db.commit()

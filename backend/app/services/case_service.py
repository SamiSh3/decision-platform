"""Case service."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.constants import CaseStatus
from app.repositories.case_repository import CaseRepository
from app.repositories.domain_repository import DomainRepository
from app.schemas.case import CaseCreate, CaseRead, CaseUpdate
from app.schemas.common import Page, PageParams


class CaseService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CaseRepository(db)
        self.domain_repo = DomainRepository(db)

    def create(self, payload: CaseCreate, owner_id: uuid.UUID) -> CaseRead:
        if self.domain_repo.get(payload.domain_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found")
        data = payload.model_dump()
        data["owner_id"] = owner_id
        data["status"] = CaseStatus.DRAFT
        instance = self.repo.create(data, actor_id=owner_id)
        self.db.commit()
        return CaseRead.model_validate(instance)

    def get(self, entity_id: uuid.UUID) -> CaseRead:
        return CaseRead.model_validate(self.repo.get_or_404(entity_id))

    def list(self, params: PageParams, filters: dict | None = None) -> Page[CaseRead]:
        items, total = self.repo.list(
            filters=filters,
            page=params.page,
            page_size=params.page_size,
            sort_by=params.sort_by,
            sort_dir=params.sort_dir,
        )
        return Page.create(
            [CaseRead.model_validate(i) for i in items], total, params.page, params.page_size
        )

    def update(
        self, entity_id: uuid.UUID, payload: CaseUpdate, actor_id: uuid.UUID | None
    ) -> CaseRead:
        instance = self.repo.get_or_404(entity_id)
        instance = self.repo.update(
            instance, payload.model_dump(exclude_unset=True), actor_id=actor_id
        )
        self.db.commit()
        return CaseRead.model_validate(instance)

    def soft_delete(self, entity_id: uuid.UUID, actor_id: uuid.UUID | None) -> None:
        instance = self.repo.get_or_404(entity_id)
        self.repo.soft_delete(instance, actor_id=actor_id)
        self.db.commit()

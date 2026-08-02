"""Expert service."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.expert_repository import ExpertRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import Page, PageParams
from app.schemas.expert import ExpertCreate, ExpertRead, ExpertUpdate


class ExpertService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ExpertRepository(db)
        self.user_repo = UserRepository(db)

    def create(self, payload: ExpertCreate, actor_id: uuid.UUID | None) -> ExpertRead:
        user = self.user_repo.get(payload.user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if self.repo.get_by_user_id(payload.user_id) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Expert profile already exists for user",
            )
        instance = self.repo.create(payload.model_dump(), actor_id=actor_id)
        self.db.commit()
        return ExpertRead.model_validate(instance)

    def get(self, entity_id: uuid.UUID) -> ExpertRead:
        return ExpertRead.model_validate(self.repo.get_or_404(entity_id))

    def list(self, params: PageParams, filters: dict | None = None) -> Page[ExpertRead]:
        items, total = self.repo.list(
            filters=filters,
            page=params.page,
            page_size=params.page_size,
            sort_by=params.sort_by,
            sort_dir=params.sort_dir,
        )
        return Page.create(
            [ExpertRead.model_validate(i) for i in items], total, params.page, params.page_size
        )

    def update(
        self, entity_id: uuid.UUID, payload: ExpertUpdate, actor_id: uuid.UUID | None
    ) -> ExpertRead:
        instance = self.repo.get_or_404(entity_id)
        instance = self.repo.update(
            instance, payload.model_dump(exclude_unset=True), actor_id=actor_id
        )
        self.db.commit()
        return ExpertRead.model_validate(instance)

    def soft_delete(self, entity_id: uuid.UUID, actor_id: uuid.UUID | None) -> None:
        instance = self.repo.get_or_404(entity_id)
        self.repo.soft_delete(instance, actor_id=actor_id)
        self.db.commit()

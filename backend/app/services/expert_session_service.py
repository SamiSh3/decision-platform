"""ExpertSession service."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.expert_repository import ExpertRepository
from app.repositories.expert_session_repository import ExpertSessionRepository
from app.repositories.questionnaire_repository import QuestionnaireRepository
from app.schemas.common import Page, PageParams
from app.schemas.expert_session import (
    ExpertSessionCreate,
    ExpertSessionRead,
    ExpertSessionUpdate,
)


class ExpertSessionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ExpertSessionRepository(db)
        self.expert_repo = ExpertRepository(db)
        self.questionnaire_repo = QuestionnaireRepository(db)

    def create(self, payload: ExpertSessionCreate, actor_id: uuid.UUID | None) -> ExpertSessionRead:
        if self.expert_repo.get(payload.expert_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expert not found")
        if self.questionnaire_repo.get(payload.questionnaire_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Questionnaire not found"
            )
        instance = self.repo.create(payload.model_dump(), actor_id=actor_id)
        self.db.commit()
        return ExpertSessionRead.model_validate(instance)

    def get(self, entity_id: uuid.UUID) -> ExpertSessionRead:
        return ExpertSessionRead.model_validate(self.repo.get_or_404(entity_id))

    def list(self, params: PageParams, filters: dict | None = None) -> Page[ExpertSessionRead]:
        items, total = self.repo.list(
            filters=filters,
            page=params.page,
            page_size=params.page_size,
            sort_by=params.sort_by,
            sort_dir=params.sort_dir,
        )
        return Page.create(
            [ExpertSessionRead.model_validate(i) for i in items],
            total,
            params.page,
            params.page_size,
        )

    def update(
        self, entity_id: uuid.UUID, payload: ExpertSessionUpdate, actor_id: uuid.UUID | None
    ) -> ExpertSessionRead:
        instance = self.repo.get_or_404(entity_id)
        instance = self.repo.update(
            instance, payload.model_dump(exclude_unset=True), actor_id=actor_id
        )
        self.db.commit()
        return ExpertSessionRead.model_validate(instance)

    def soft_delete(self, entity_id: uuid.UUID, actor_id: uuid.UUID | None) -> None:
        instance = self.repo.get_or_404(entity_id)
        self.repo.soft_delete(instance, actor_id=actor_id)
        self.db.commit()

"""Response and Evidence services - the knowledge-capture write path."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.case_repository import CaseRepository
from app.repositories.expert_repository import ExpertRepository
from app.repositories.questionnaire_repository import QuestionRepository
from app.repositories.response_repository import (
    EvidenceRepository,
    KnowledgeSourceRepository,
    ResponseRepository,
)
from app.schemas.common import Page, PageParams
from app.schemas.evidence import (
    EvidenceCreate,
    EvidenceRead,
    EvidenceUpdate,
    KnowledgeSourceCreate,
    KnowledgeSourceRead,
    KnowledgeSourceUpdate,
)
from app.schemas.response import ResponseCreate, ResponseRead, ResponseUpdate


class ResponseService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ResponseRepository(db)
        self.case_repo = CaseRepository(db)
        self.question_repo = QuestionRepository(db)
        self.expert_repo = ExpertRepository(db)

    def create(self, payload: ResponseCreate, actor_id: uuid.UUID | None) -> ResponseRead:
        if self.case_repo.get(payload.case_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
        if self.question_repo.get(payload.question_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
        if self.expert_repo.get(payload.expert_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expert not found")
        instance = self.repo.create(payload.model_dump(), actor_id=actor_id)
        self.db.commit()
        return ResponseRead.model_validate(instance)

    def get(self, entity_id: uuid.UUID) -> ResponseRead:
        return ResponseRead.model_validate(self.repo.get_or_404(entity_id))

    def list_for_case(self, case_id: uuid.UUID) -> list[ResponseRead]:
        items = self.repo.list_for_case(case_id)
        return [ResponseRead.model_validate(i) for i in items]

    def list(self, params: PageParams, filters: dict | None = None) -> Page[ResponseRead]:
        items, total = self.repo.list(
            filters=filters,
            page=params.page,
            page_size=params.page_size,
            sort_by=params.sort_by,
            sort_dir=params.sort_dir,
        )
        return Page.create(
            [ResponseRead.model_validate(i) for i in items], total, params.page, params.page_size
        )

    def update(
        self, entity_id: uuid.UUID, payload: ResponseUpdate, actor_id: uuid.UUID | None
    ) -> ResponseRead:
        instance = self.repo.get_or_404(entity_id)
        instance = self.repo.update(
            instance, payload.model_dump(exclude_unset=True), actor_id=actor_id
        )
        self.db.commit()
        return ResponseRead.model_validate(instance)

    def soft_delete(self, entity_id: uuid.UUID, actor_id: uuid.UUID | None) -> None:
        instance = self.repo.get_or_404(entity_id)
        self.repo.soft_delete(instance, actor_id=actor_id)
        self.db.commit()


class EvidenceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = EvidenceRepository(db)
        self.response_repo = ResponseRepository(db)
        self.source_repo = KnowledgeSourceRepository(db)

    def create(self, payload: EvidenceCreate, actor_id: uuid.UUID | None) -> EvidenceRead:
        if self.response_repo.get(payload.response_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Response not found")
        instance = self.repo.create(payload.model_dump(), actor_id=actor_id)
        self.db.commit()
        return EvidenceRead.model_validate(instance)

    def get(self, entity_id: uuid.UUID) -> EvidenceRead:
        return EvidenceRead.model_validate(self.repo.get_or_404(entity_id))

    def list(self, params: PageParams, filters: dict | None = None) -> Page[EvidenceRead]:
        items, total = self.repo.list(
            filters=filters,
            page=params.page,
            page_size=params.page_size,
            sort_by=params.sort_by,
            sort_dir=params.sort_dir,
        )
        return Page.create(
            [EvidenceRead.model_validate(i) for i in items], total, params.page, params.page_size
        )

    def update(
        self, entity_id: uuid.UUID, payload: EvidenceUpdate, actor_id: uuid.UUID | None
    ) -> EvidenceRead:
        instance = self.repo.get_or_404(entity_id)
        instance = self.repo.update(
            instance, payload.model_dump(exclude_unset=True), actor_id=actor_id
        )
        self.db.commit()
        return EvidenceRead.model_validate(instance)

    def soft_delete(self, entity_id: uuid.UUID, actor_id: uuid.UUID | None) -> None:
        instance = self.repo.get_or_404(entity_id)
        self.repo.soft_delete(instance, actor_id=actor_id)
        self.db.commit()


class KnowledgeSourceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = KnowledgeSourceRepository(db)

    def create(
        self, payload: KnowledgeSourceCreate, actor_id: uuid.UUID | None
    ) -> KnowledgeSourceRead:
        instance = self.repo.create(payload.model_dump(), actor_id=actor_id)
        self.db.commit()
        return KnowledgeSourceRead.model_validate(instance)

    def get(self, entity_id: uuid.UUID) -> KnowledgeSourceRead:
        return KnowledgeSourceRead.model_validate(self.repo.get_or_404(entity_id))

    def list(self, params: PageParams, filters: dict | None = None) -> Page[KnowledgeSourceRead]:
        items, total = self.repo.list(
            filters=filters,
            page=params.page,
            page_size=params.page_size,
            sort_by=params.sort_by,
            sort_dir=params.sort_dir,
        )
        return Page.create(
            [KnowledgeSourceRead.model_validate(i) for i in items],
            total,
            params.page,
            params.page_size,
        )

    def update(
        self, entity_id: uuid.UUID, payload: KnowledgeSourceUpdate, actor_id: uuid.UUID | None
    ) -> KnowledgeSourceRead:
        instance = self.repo.get_or_404(entity_id)
        instance = self.repo.update(
            instance, payload.model_dump(exclude_unset=True), actor_id=actor_id
        )
        self.db.commit()
        return KnowledgeSourceRead.model_validate(instance)

    def soft_delete(self, entity_id: uuid.UUID, actor_id: uuid.UUID | None) -> None:
        instance = self.repo.get_or_404(entity_id)
        self.repo.soft_delete(instance, actor_id=actor_id)
        self.db.commit()

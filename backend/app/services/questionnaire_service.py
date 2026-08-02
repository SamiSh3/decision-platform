"""Questionnaire and Question services - part of the knowledge capture domain."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.audit_repository import VersionHistoryRepository
from app.repositories.domain_repository import DomainRepository
from app.repositories.questionnaire_repository import (
    QuestionnaireRepository,
    QuestionOptionRepository,
    QuestionRepository,
)
from app.schemas.common import Page, PageParams
from app.schemas.questionnaire import (
    QuestionCreate,
    QuestionnaireCreate,
    QuestionnaireRead,
    QuestionnaireUpdate,
    QuestionRead,
    QuestionUpdate,
)


class QuestionnaireService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = QuestionnaireRepository(db)
        self.domain_repo = DomainRepository(db)
        self.question_repo = QuestionRepository(db)
        self.option_repo = QuestionOptionRepository(db)
        self.version_repo = VersionHistoryRepository(db)

    def create(self, payload: QuestionnaireCreate, actor_id: uuid.UUID | None) -> QuestionnaireRead:
        if self.domain_repo.get(payload.domain_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found")
        instance = self.repo.create(payload.model_dump(), actor_id=actor_id)
        self.version_repo.create(
            {
                "entity_type": "questionnaire",
                "entity_id": instance.id,
                "version": instance.version,
                "snapshot": payload.model_dump(mode="json"),
                "change_summary": "Initial version created",
            },
            actor_id=actor_id,
        )
        self.db.commit()
        refreshed = self.repo.get_with_questions(instance.id)
        return QuestionnaireRead.model_validate(refreshed)

    def get(self, entity_id: uuid.UUID) -> QuestionnaireRead:
        instance = self.repo.get_with_questions(entity_id)
        if instance is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Questionnaire not found"
            )
        return QuestionnaireRead.model_validate(instance)

    def list(self, params: PageParams, filters: dict | None = None) -> Page[QuestionnaireRead]:
        items, total = self.repo.list(
            filters=filters,
            page=params.page,
            page_size=params.page_size,
            sort_by=params.sort_by,
            sort_dir=params.sort_dir,
        )
        detailed = [self.repo.get_with_questions(i.id) for i in items]
        return Page.create(
            [QuestionnaireRead.model_validate(i) for i in detailed if i is not None],
            total,
            params.page,
            params.page_size,
        )

    def update(
        self, entity_id: uuid.UUID, payload: QuestionnaireUpdate, actor_id: uuid.UUID | None
    ) -> QuestionnaireRead:
        instance = self.repo.get_or_404(entity_id)
        self.repo.update(instance, payload.model_dump(exclude_unset=True), actor_id=actor_id)
        self.db.commit()
        return self.get(entity_id)

    def soft_delete(self, entity_id: uuid.UUID, actor_id: uuid.UUID | None) -> None:
        instance = self.repo.get_or_404(entity_id)
        self.repo.soft_delete(instance, actor_id=actor_id)
        self.db.commit()

    def add_question(
        self, questionnaire_id: uuid.UUID, payload: QuestionCreate, actor_id: uuid.UUID | None
    ) -> QuestionRead:
        if self.repo.get(questionnaire_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Questionnaire not found"
            )
        data = payload.model_dump(exclude={"options"})
        data["questionnaire_id"] = questionnaire_id
        question = self.question_repo.create(data, actor_id=actor_id)
        for option in payload.options:
            option_data = option.model_dump()
            option_data["question_id"] = question.id
            self.option_repo.create(option_data, actor_id=actor_id)
        self.db.commit()
        refreshed = self.question_repo.get(question.id)
        return QuestionRead.model_validate(refreshed)

    def update_question(
        self, question_id: uuid.UUID, payload: QuestionUpdate, actor_id: uuid.UUID | None
    ) -> QuestionRead:
        instance = self.question_repo.get_or_404(question_id)
        instance = self.question_repo.update(
            instance, payload.model_dump(exclude_unset=True), actor_id=actor_id
        )
        self.db.commit()
        return QuestionRead.model_validate(instance)

    def create_new_version(
        self, questionnaire_id: uuid.UUID, actor_id: uuid.UUID | None
    ) -> QuestionnaireRead:
        """Creates a new, inactive draft version of an existing questionnaire,
        copying its questions and options. The prior version is left untouched
        and keeps its `is_active` status, mirroring Rule's immutable versioning
        so questionnaires already administered to experts are never mutated."""
        existing = self.repo.get_with_questions(questionnaire_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Questionnaire not found"
            )

        new_questionnaire = self.repo.create(
            {
                "domain_id": existing.domain_id,
                "code": existing.code,
                "title": existing.title,
                "description": existing.description,
                "version": existing.version + 1,
                "is_active": False,
            },
            actor_id=actor_id,
        )

        for question in existing.questions:
            new_question = self.question_repo.create(
                {
                    "questionnaire_id": new_questionnaire.id,
                    "code": question.code,
                    "text": question.text,
                    "help_text": question.help_text,
                    "question_type": question.question_type,
                    "display_order": question.display_order,
                    "is_required": question.is_required,
                    "default_importance": question.default_importance,
                    "default_risk": question.default_risk,
                },
                actor_id=actor_id,
            )
            for option in question.options:
                self.option_repo.create(
                    {
                        "question_id": new_question.id,
                        "value": option.value,
                        "label": option.label,
                        "display_order": option.display_order,
                        "score_weight": option.score_weight,
                    },
                    actor_id=actor_id,
                )

        self.version_repo.create(
            {
                "entity_type": "questionnaire",
                "entity_id": new_questionnaire.id,
                "version": new_questionnaire.version,
                "snapshot": {
                    "code": existing.code,
                    "title": existing.title,
                    "based_on_version": existing.version,
                },
                "change_summary": f"Forked from version {existing.version}",
            },
            actor_id=actor_id,
        )
        self.db.commit()
        return self.get(new_questionnaire.id)

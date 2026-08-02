"""Questionnaire, Question and QuestionOption repositories."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.question import Question, QuestionOption
from app.models.questionnaire import Questionnaire
from app.repositories.base import BaseRepository


class QuestionnaireRepository(BaseRepository[Questionnaire]):
    model = Questionnaire

    def get_with_questions(self, entity_id: uuid.UUID) -> Questionnaire | None:
        stmt = (
            select(Questionnaire)
            .where(Questionnaire.id == entity_id, Questionnaire.is_deleted.is_(False))
            .options(selectinload(Questionnaire.questions).selectinload(Question.options))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_active_for_domain(self, domain_id: uuid.UUID, code: str) -> Questionnaire | None:
        stmt = (
            select(Questionnaire)
            .where(
                Questionnaire.domain_id == domain_id,
                Questionnaire.code == code,
                Questionnaire.is_active.is_(True),
                Questionnaire.is_deleted.is_(False),
            )
            .order_by(Questionnaire.version.desc())
        )
        return self.db.execute(stmt).scalars().first()


class QuestionRepository(BaseRepository[Question]):
    model = Question

    def list_for_questionnaire(self, questionnaire_id: uuid.UUID) -> list[Question]:
        stmt = (
            select(Question)
            .where(Question.questionnaire_id == questionnaire_id, Question.is_deleted.is_(False))
            .options(selectinload(Question.options))
            .order_by(Question.display_order)
        )
        return list(self.db.execute(stmt).scalars().all())


class QuestionOptionRepository(BaseRepository[QuestionOption]):
    model = QuestionOption

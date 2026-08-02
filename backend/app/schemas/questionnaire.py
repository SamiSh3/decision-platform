"""Questionnaire, Question and QuestionOption schemas."""

from __future__ import annotations

import uuid

from pydantic import Field

from app.core.constants import ImportanceLevel, QuestionType, RiskLevel
from app.schemas.common import AuditFieldsSchema, ORMBase


class QuestionOptionCreate(ORMBase):
    value: str = Field(min_length=1, max_length=100)
    label: str = Field(min_length=1, max_length=255)
    display_order: int = 0
    score_weight: float = 0.0


class QuestionOptionRead(AuditFieldsSchema):
    question_id: uuid.UUID
    value: str
    label: str
    display_order: int
    score_weight: float


class QuestionCreate(ORMBase):
    code: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1)
    help_text: str | None = None
    question_type: QuestionType
    display_order: int = 0
    is_required: bool = True
    default_importance: ImportanceLevel = ImportanceLevel.MEDIUM
    default_risk: RiskLevel = RiskLevel.LOW
    options: list[QuestionOptionCreate] = Field(default_factory=list)


class QuestionUpdate(ORMBase):
    text: str | None = None
    help_text: str | None = None
    display_order: int | None = None
    is_required: bool | None = None
    default_importance: ImportanceLevel | None = None
    default_risk: RiskLevel | None = None


class QuestionRead(AuditFieldsSchema):
    questionnaire_id: uuid.UUID
    code: str
    text: str
    help_text: str | None = None
    question_type: QuestionType
    display_order: int
    is_required: bool
    default_importance: ImportanceLevel
    default_risk: RiskLevel
    options: list[QuestionOptionRead] = Field(default_factory=list)


class QuestionnaireCreate(ORMBase):
    domain_id: uuid.UUID
    code: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    version: int = 1
    is_active: bool = True


class QuestionnaireUpdate(ORMBase):
    title: str | None = None
    description: str | None = None
    is_active: bool | None = None


class QuestionnaireRead(AuditFieldsSchema):
    domain_id: uuid.UUID
    code: str
    title: str
    description: str | None = None
    version: int
    is_active: bool
    questions: list[QuestionRead] = Field(default_factory=list)

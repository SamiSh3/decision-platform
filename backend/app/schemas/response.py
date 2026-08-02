"""Response (expert answer) schemas."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import Field

from app.core.constants import ImportanceLevel, RiskLevel
from app.schemas.common import AuditFieldsSchema, ORMBase
from app.schemas.evidence import EvidenceRead


class ResponseCreate(ORMBase):
    case_id: uuid.UUID
    question_id: uuid.UUID
    expert_id: uuid.UUID
    answer_value: dict[str, Any]
    confidence: float = Field(default=1.0, ge=0, le=1)
    reasoning: str | None = None
    conditions: str | None = None
    exceptions: str | None = None
    importance: ImportanceLevel = ImportanceLevel.MEDIUM
    risk: RiskLevel = RiskLevel.LOW
    notes: str | None = None
    references: list[str] = Field(default_factory=list)


class ResponseUpdate(ORMBase):
    answer_value: dict[str, Any] | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    reasoning: str | None = None
    conditions: str | None = None
    exceptions: str | None = None
    importance: ImportanceLevel | None = None
    risk: RiskLevel | None = None
    notes: str | None = None
    references: list[str] | None = None


class ResponseRead(AuditFieldsSchema):
    case_id: uuid.UUID
    question_id: uuid.UUID
    expert_id: uuid.UUID
    answer_value: dict[str, Any]
    confidence: float
    reasoning: str | None = None
    conditions: str | None = None
    exceptions: str | None = None
    importance: ImportanceLevel
    risk: RiskLevel
    notes: str | None = None
    references: list[str] = Field(default_factory=list)
    evidence_items: list[EvidenceRead] = Field(default_factory=list)

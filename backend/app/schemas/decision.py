"""ConfidenceScore and DecisionResult read schemas (engine-generated, read-only)."""

from __future__ import annotations

import uuid
from typing import Any

from app.core.constants import RecommendationLabel
from app.schemas.common import AuditFieldsSchema


class ConfidenceScoreRead(AuditFieldsSchema):
    case_id: uuid.UUID
    rule_id: uuid.UUID
    raw_score: float
    normalized_score: float
    contributing_expert_count: int
    conflict_detected: bool
    calculation_trace: dict[str, Any]


class DecisionResultRead(AuditFieldsSchema):
    case_id: uuid.UUID
    recommendation: RecommendationLabel
    overall_score: float
    overall_confidence: float
    explanation: dict[str, Any]
    engine_version: str

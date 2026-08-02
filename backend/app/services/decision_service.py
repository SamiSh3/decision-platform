"""Decision service - triggers the DecisionEngine and exposes results/confidence scores."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.decision_engine.engine import DecisionEngine
from app.repositories.decision_repository import ConfidenceScoreRepository, DecisionResultRepository
from app.schemas.decision import ConfidenceScoreRead, DecisionResultRead
from app.utils.explanation_formatter import format_decision_explanation


class DecisionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.engine = DecisionEngine(db)
        self.result_repo = DecisionResultRepository(db)
        self.confidence_repo = ConfidenceScoreRepository(db)

    def evaluate(self, case_id: uuid.UUID, actor_id: uuid.UUID | None) -> DecisionResultRead:
        raw = self.engine.evaluate_case(case_id, actor_id=actor_id)
        return DecisionResultRead(
            id=raw["id"],
            created_at=raw["created_at"],
            updated_at=raw["updated_at"],
            created_by=raw["created_by"],
            updated_by=raw["updated_by"],
            is_deleted=raw["is_deleted"],
            case_id=raw["case_id"],
            recommendation=raw["recommendation"],
            overall_score=raw["overall_score"],
            overall_confidence=raw["overall_confidence"],
            explanation=raw["explanation"],
            engine_version=raw["engine_version"],
        )

    def get(self, entity_id: uuid.UUID) -> DecisionResultRead:
        instance = self.result_repo.get_or_404(entity_id)
        return DecisionResultRead.model_validate(instance)

    def get_explanation_text(self, entity_id: uuid.UUID) -> str:
        instance = self.result_repo.get_or_404(entity_id)
        return format_decision_explanation(
            recommendation=(
                instance.recommendation.value
                if hasattr(instance.recommendation, "value")
                else instance.recommendation
            ),
            overall_score=float(instance.overall_score),
            overall_confidence=float(instance.overall_confidence),
            explanation=instance.explanation,
        )

    def list_for_case(self, case_id: uuid.UUID) -> list[DecisionResultRead]:
        items = self.result_repo.list_for_case(case_id)
        return [DecisionResultRead.model_validate(i) for i in items]

    def get_latest_for_case(self, case_id: uuid.UUID) -> DecisionResultRead | None:
        instance = self.result_repo.get_latest_for_case(case_id)
        if instance is None:
            return None
        return DecisionResultRead.model_validate(instance)

    def list_confidence_scores_for_case(self, case_id: uuid.UUID) -> list[ConfidenceScoreRead]:
        items = self.confidence_repo.list_for_case(case_id)
        return [ConfidenceScoreRead.model_validate(i) for i in items]

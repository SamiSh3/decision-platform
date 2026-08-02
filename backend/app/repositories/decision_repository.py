"""ConfidenceScore and DecisionResult repositories."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models.confidence_score import ConfidenceScore
from app.models.decision_result import DecisionResult
from app.repositories.base import BaseRepository


class ConfidenceScoreRepository(BaseRepository[ConfidenceScore]):
    model = ConfidenceScore

    def list_for_case(self, case_id: uuid.UUID) -> list[ConfidenceScore]:
        stmt = select(ConfidenceScore).where(
            ConfidenceScore.case_id == case_id, ConfidenceScore.is_deleted.is_(False)
        )
        return list(self.db.execute(stmt).scalars().all())


class DecisionResultRepository(BaseRepository[DecisionResult]):
    model = DecisionResult

    def list_for_case(self, case_id: uuid.UUID) -> list[DecisionResult]:
        stmt = (
            select(DecisionResult)
            .where(DecisionResult.case_id == case_id, DecisionResult.is_deleted.is_(False))
            .order_by(DecisionResult.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_latest_for_case(self, case_id: uuid.UUID) -> DecisionResult | None:
        stmt = (
            select(DecisionResult)
            .where(DecisionResult.case_id == case_id, DecisionResult.is_deleted.is_(False))
            .order_by(DecisionResult.created_at.desc())
        )
        return self.db.execute(stmt).scalars().first()

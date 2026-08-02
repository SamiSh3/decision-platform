"""ConfidenceScore model - explainable per-rule, per-case aggregated confidence value
produced by the decision engine while combining (possibly conflicting) expert opinions."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel

if TYPE_CHECKING:
    from app.models.case import Case
    from app.models.rule import Rule


class ConfidenceScore(BaseModel):
    __tablename__ = "confidence_scores"

    case_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    raw_score: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    normalized_score: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    contributing_expert_count: Mapped[int] = mapped_column(nullable=False, default=0)
    conflict_detected: Mapped[bool] = mapped_column(nullable=False, default=False)
    calculation_trace: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    case: Mapped[Case] = relationship("Case")
    rule: Mapped[Rule] = relationship("Rule")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<ConfidenceScore case={self.case_id} rule={self.rule_id} "
            f"score={self.normalized_score}>"
        )

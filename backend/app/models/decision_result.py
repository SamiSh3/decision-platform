"""DecisionResult model - the final, explainable recommendation for a case."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import RecommendationLabel
from app.database.base import BaseModel

if TYPE_CHECKING:
    from app.models.case import Case


class DecisionResult(BaseModel):
    __tablename__ = "decision_results"

    case_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recommendation: Mapped[RecommendationLabel] = mapped_column(
        SAEnum(RecommendationLabel, name="recommendation_label_enum"), nullable=False
    )
    overall_score: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    overall_confidence: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    explanation: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    engine_version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0.0")

    case: Mapped[Case] = relationship("Case", back_populates="decision_results")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DecisionResult case={self.case_id} rec={self.recommendation}>"

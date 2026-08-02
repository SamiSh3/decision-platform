"""Response model - an expert's answer to a question for a specific case.

Captures the full knowledge-capture payload required by the platform: confidence,
reasoning, evidence, conditions, exceptions, importance, risk, notes and references.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Numeric, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ImportanceLevel, RiskLevel
from app.database.base import BaseModel

if TYPE_CHECKING:
    from app.models.case import Case
    from app.models.evidence import Evidence
    from app.models.expert import Expert
    from app.models.question import Question


class Response(BaseModel):
    __tablename__ = "responses"
    __table_args__ = (
        UniqueConstraint(
            "case_id", "question_id", "expert_id", name="uq_response_case_question_expert"
        ),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    expert_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("experts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    answer_value: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    # Knowledge-capture fields
    confidence: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False, default=1.0)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    exceptions: Mapped[str | None] = mapped_column(Text, nullable=True)
    importance: Mapped[ImportanceLevel] = mapped_column(
        SAEnum(ImportanceLevel, name="response_importance_enum"),
        nullable=False,
        default=ImportanceLevel.MEDIUM,
    )
    risk: Mapped[RiskLevel] = mapped_column(
        SAEnum(RiskLevel, name="response_risk_enum"), nullable=False, default=RiskLevel.LOW
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    references: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)

    case: Mapped[Case] = relationship("Case", back_populates="responses")
    question: Mapped[Question] = relationship("Question", back_populates="responses")
    expert: Mapped[Expert] = relationship("Expert", back_populates="responses")
    evidence_items: Mapped[list[Evidence]] = relationship(
        "Evidence", back_populates="response", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Response case={self.case_id} question={self.question_id}>"

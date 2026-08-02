"""Rule, RuleCondition and RuleOutcome models - the decision engine's rule base."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import OutcomeDirection, RuleOperator, RuleStatus
from app.database.base import BaseModel

if TYPE_CHECKING:
    from app.models.domain import Domain


class Rule(BaseModel):
    __tablename__ = "rules"
    __table_args__ = (
        UniqueConstraint("domain_id", "code", "version", name="uq_rule_domain_code_version"),
    )

    domain_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("domains.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[RuleStatus] = mapped_column(
        SAEnum(RuleStatus, name="rule_status_enum"),
        nullable=False,
        default=RuleStatus.DRAFT,
        index=True,
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    weight: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False, default=1.0)

    domain: Mapped[Domain] = relationship("Domain", back_populates="rules")
    conditions: Mapped[list[RuleCondition]] = relationship(
        "RuleCondition", back_populates="rule", cascade="all, delete-orphan"
    )
    outcomes: Mapped[list[RuleOutcome]] = relationship(
        "RuleOutcome", back_populates="rule", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Rule {self.code} v{self.version}>"


class RuleCondition(BaseModel):
    """A single condition that must hold for a rule to be applicable to a case.

    `attribute_path` addresses either a question code (``question:<code>``) or a
    top-level case subject_data field (``subject:<field>``), evaluated by the
    decision engine's matcher.
    """

    __tablename__ = "rule_conditions"

    rule_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attribute_path: Mapped[str] = mapped_column(String(255), nullable=False)
    operator: Mapped[RuleOperator] = mapped_column(
        SAEnum(RuleOperator, name="rule_operator_enum"), nullable=False
    )
    value: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    group_id: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )  # OR-groups of AND-conditions

    rule: Mapped[Rule] = relationship("Rule", back_populates="conditions")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<RuleCondition {self.attribute_path} {self.operator}>"


class RuleOutcome(BaseModel):
    """The recommendation contribution produced when a rule fires."""

    __tablename__ = "rule_outcomes"

    rule_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    direction: Mapped[OutcomeDirection] = mapped_column(
        SAEnum(OutcomeDirection, name="outcome_direction_enum"), nullable=False
    )
    score_impact: Mapped[float] = mapped_column(
        Numeric(5, 3), nullable=False
    )  # e.g. -1.000 .. 1.000
    explanation_template: Mapped[str] = mapped_column(Text, nullable=False)

    rule: Mapped[Rule] = relationship("Rule", back_populates="outcomes")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<RuleOutcome {self.direction}>"

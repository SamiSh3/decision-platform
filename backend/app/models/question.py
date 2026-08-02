"""Question and QuestionOption models."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ImportanceLevel, QuestionType, RiskLevel
from app.database.base import BaseModel

if TYPE_CHECKING:
    from app.models.questionnaire import Questionnaire
    from app.models.response import Response


class Question(BaseModel):
    __tablename__ = "questions"
    __table_args__ = (
        UniqueConstraint("questionnaire_id", "code", name="uq_question_questionnaire_code"),
    )

    questionnaire_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("questionnaires.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    help_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    question_type: Mapped[QuestionType] = mapped_column(
        SAEnum(QuestionType, name="question_type_enum"), nullable=False
    )
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_required: Mapped[bool] = mapped_column(default=True, nullable=False)
    default_importance: Mapped[ImportanceLevel] = mapped_column(
        SAEnum(ImportanceLevel, name="importance_level_enum"),
        nullable=False,
        default=ImportanceLevel.MEDIUM,
    )
    default_risk: Mapped[RiskLevel] = mapped_column(
        SAEnum(RiskLevel, name="risk_level_enum"), nullable=False, default=RiskLevel.LOW
    )

    questionnaire: Mapped[Questionnaire] = relationship("Questionnaire", back_populates="questions")
    options: Mapped[list[QuestionOption]] = relationship(
        "QuestionOption",
        back_populates="question",
        order_by="QuestionOption.display_order",
        cascade="all, delete-orphan",
    )
    responses: Mapped[list[Response]] = relationship("Response", back_populates="question")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Question {self.code}>"


class QuestionOption(BaseModel):
    __tablename__ = "question_options"
    __table_args__ = (UniqueConstraint("question_id", "value", name="uq_question_option_value"),)

    question_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    value: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    score_weight: Mapped[float] = mapped_column(nullable=False, default=0.0)

    question: Mapped[Question] = relationship("Question", back_populates="options")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<QuestionOption {self.value}>"

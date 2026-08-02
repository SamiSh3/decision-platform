"""Questionnaire model - a versioned set of questions for a domain."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel

if TYPE_CHECKING:
    from app.models.domain import Domain
    from app.models.question import Question


class Questionnaire(BaseModel):
    __tablename__ = "questionnaires"
    __table_args__ = (
        UniqueConstraint(
            "domain_id", "code", "version", name="uq_questionnaire_domain_code_version"
        ),
    )

    domain_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("domains.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    domain: Mapped[Domain] = relationship("Domain", back_populates="questionnaires")
    questions: Mapped[list[Question]] = relationship(
        "Question",
        back_populates="questionnaire",
        order_by="Question.display_order",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Questionnaire {self.code} v{self.version}>"

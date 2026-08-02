"""Domain model - top-level decision domain (Used Car Purchase, Real Estate, ...)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel

if TYPE_CHECKING:
    from app.models.case import Case
    from app.models.questionnaire import Questionnaire
    from app.models.rule import Rule


class Domain(BaseModel):
    __tablename__ = "domains"

    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    questionnaires: Mapped[list[Questionnaire]] = relationship(
        "Questionnaire", back_populates="domain"
    )
    rules: Mapped[list[Rule]] = relationship("Rule", back_populates="domain")
    cases: Mapped[list[Case]] = relationship("Case", back_populates="domain")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Domain {self.code}>"

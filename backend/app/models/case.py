"""Case model - a concrete decision instance within a domain (e.g. one car purchase)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import CaseStatus
from app.database.base import BaseModel

if TYPE_CHECKING:
    from app.models.attachment import Attachment
    from app.models.decision_result import DecisionResult
    from app.models.domain import Domain
    from app.models.response import Response


class Case(BaseModel):
    __tablename__ = "cases"

    domain_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("domains.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[CaseStatus] = mapped_column(
        SAEnum(CaseStatus, name="case_status_enum"),
        nullable=False,
        default=CaseStatus.DRAFT,
        index=True,
    )
    subject_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    domain: Mapped[Domain] = relationship("Domain", back_populates="cases")
    responses: Mapped[list[Response]] = relationship(
        "Response", back_populates="case", cascade="all, delete-orphan"
    )
    decision_results: Mapped[list[DecisionResult]] = relationship(
        "DecisionResult", back_populates="case", cascade="all, delete-orphan"
    )
    attachments: Mapped[list[Attachment]] = relationship(
        "Attachment",
        primaryjoin="and_(Attachment.entity_type=='case', "
        "foreign(Attachment.entity_id)==Case.id)",
        viewonly=True,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Case {self.title}>"

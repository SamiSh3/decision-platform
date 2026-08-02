"""ExpertSession model - a scheduled/completed knowledge-capture session with an expert."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ExpertSessionStatus
from app.database.base import BaseModel

if TYPE_CHECKING:
    from app.models.expert import Expert
    from app.models.questionnaire import Questionnaire


class ExpertSession(BaseModel):
    __tablename__ = "expert_sessions"

    expert_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("experts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    questionnaire_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("questionnaires.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[ExpertSessionStatus] = mapped_column(
        SAEnum(ExpertSessionStatus, name="expert_session_status_enum"),
        nullable=False,
        default=ExpertSessionStatus.SCHEDULED,
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    expert: Mapped[Expert] = relationship("Expert", back_populates="sessions")
    questionnaire: Mapped[Questionnaire] = relationship("Questionnaire")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ExpertSession {self.id}>"

"""Expert profile model - additional attributes for users with the expert role."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel

if TYPE_CHECKING:
    from app.models.expert_session import ExpertSession
    from app.models.response import Response
    from app.models.user import User


class Expert(BaseModel):
    __tablename__ = "experts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    specialty: Mapped[str] = mapped_column(String(255), nullable=False)
    years_experience: Mapped[int] = mapped_column(nullable=False, default=0)
    credentials: Mapped[str | None] = mapped_column(Text, nullable=True)
    weight: Mapped[float] = mapped_column(
        Numeric(4, 3), nullable=False, default=1.0
    )  # relative trust weight used by the decision engine, e.g. 0.000-9.999
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship(
        "User", back_populates="expert_profile", foreign_keys=[user_id]
    )
    responses: Mapped[list[Response]] = relationship("Response", back_populates="expert")
    sessions: Mapped[list[ExpertSession]] = relationship("ExpertSession", back_populates="expert")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Expert {self.specialty}>"

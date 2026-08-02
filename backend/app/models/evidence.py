"""Evidence and KnowledgeSource models."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel

if TYPE_CHECKING:
    from app.models.response import Response


class KnowledgeSource(BaseModel):
    """A reusable, citable source of knowledge (manual, standard, expert experience, article)."""

    __tablename__ = "knowledge_sources"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # e.g. manual, article, experience
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reliability_score: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False, default=0.8)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    evidence_items: Mapped[list[Evidence]] = relationship(
        "Evidence", back_populates="knowledge_source"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<KnowledgeSource {self.name}>"


class Evidence(BaseModel):
    """Supporting evidence attached to an expert response."""

    __tablename__ = "evidence"

    response_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("responses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    knowledge_source_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("knowledge_sources.id", ondelete="SET NULL"),
        nullable=True,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    reliability_score: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False, default=0.8)

    response: Mapped[Response] = relationship("Response", back_populates="evidence_items")
    knowledge_source: Mapped[KnowledgeSource | None] = relationship(
        "KnowledgeSource", back_populates="evidence_items"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Evidence {self.id}>"

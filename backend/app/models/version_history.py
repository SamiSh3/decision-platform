"""VersionHistory model - snapshot storage for versioned entities (Questionnaire, Rule)."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import BaseModel


class VersionHistory(BaseModel):
    __tablename__ = "version_histories"

    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    change_summary: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<VersionHistory {self.entity_type}#{self.entity_id} v{self.version}>"

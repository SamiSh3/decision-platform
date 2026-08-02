"""AuditLog model - immutable record of significant actions across the system."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Enum as SAEnum
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import AuditAction
from app.database.base import BaseModel


class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    action: Mapped[AuditAction] = mapped_column(
        SAEnum(AuditAction, name="audit_action_enum"), nullable=False
    )
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    metadata_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AuditLog {self.action} {self.entity_type}>"

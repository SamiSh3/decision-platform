"""AuditLog and VersionHistory read schemas (system-generated, read-only)."""

from __future__ import annotations

import uuid
from typing import Any

from app.core.constants import AuditAction
from app.schemas.common import AuditFieldsSchema


class AuditLogRead(AuditFieldsSchema):
    actor_id: uuid.UUID | None = None
    action: AuditAction
    entity_type: str
    entity_id: uuid.UUID | None = None
    metadata_payload: dict[str, Any]
    ip_address: str | None = None


class VersionHistoryRead(AuditFieldsSchema):
    entity_type: str
    entity_id: uuid.UUID
    version: int
    snapshot: dict[str, Any]
    change_summary: str | None = None

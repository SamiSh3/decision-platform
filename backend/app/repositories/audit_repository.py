"""Attachment, AuditLog and VersionHistory repositories."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models.attachment import Attachment
from app.models.audit_log import AuditLog
from app.models.version_history import VersionHistory
from app.repositories.base import BaseRepository


class AttachmentRepository(BaseRepository[Attachment]):
    model = Attachment

    def list_for_entity(self, entity_type: str, entity_id: uuid.UUID) -> list[Attachment]:
        stmt = select(Attachment).where(
            Attachment.entity_type == entity_type,
            Attachment.entity_id == entity_id,
            Attachment.is_deleted.is_(False),
        )
        return list(self.db.execute(stmt).scalars().all())


class AuditLogRepository(BaseRepository[AuditLog]):
    model = AuditLog

    def record(
        self,
        *,
        actor_id: uuid.UUID | None,
        action: str,
        entity_type: str,
        entity_id: uuid.UUID | None,
        metadata_payload: dict | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        instance = AuditLog(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_payload=metadata_payload or {},
            ip_address=ip_address,
        )
        self.db.add(instance)
        self.db.flush()
        self.db.refresh(instance)
        return instance


class VersionHistoryRepository(BaseRepository[VersionHistory]):
    model = VersionHistory

    def list_for_entity(self, entity_type: str, entity_id: uuid.UUID) -> list[VersionHistory]:
        stmt = (
            select(VersionHistory)
            .where(
                VersionHistory.entity_type == entity_type,
                VersionHistory.entity_id == entity_id,
                VersionHistory.is_deleted.is_(False),
            )
            .order_by(VersionHistory.version.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

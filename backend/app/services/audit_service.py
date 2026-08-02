"""Audit service - read access to audit logs and version history (system-generated)."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.repositories.audit_repository import AuditLogRepository, VersionHistoryRepository
from app.schemas.audit import AuditLogRead, VersionHistoryRead
from app.schemas.common import Page, PageParams


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.log_repo = AuditLogRepository(db)
        self.version_repo = VersionHistoryRepository(db)

    def list_logs(self, params: PageParams, filters: dict | None = None) -> Page[AuditLogRead]:
        items, total = self.log_repo.list(
            filters=filters,
            page=params.page,
            page_size=params.page_size,
            sort_by=params.sort_by,
            sort_dir=params.sort_dir,
        )
        return Page.create(
            [AuditLogRead.model_validate(i) for i in items], total, params.page, params.page_size
        )

    def list_versions(self, entity_type: str, entity_id: uuid.UUID) -> list[VersionHistoryRead]:
        items = self.version_repo.list_for_entity(entity_type, entity_id)
        return [VersionHistoryRead.model_validate(i) for i in items]

"""Read-only AuditLog and VersionHistory endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import require_reviewer
from app.dependencies.pagination import pagination_params
from app.models.user import User
from app.schemas.audit import AuditLogRead, VersionHistoryRead
from app.schemas.common import Page, PageParams
from app.services.audit_service import AuditService

router = APIRouter(tags=["audit"])


@router.get(
    "/audit-logs", response_model=Page[AuditLogRead], dependencies=[Depends(require_reviewer)]
)
def list_audit_logs(
    db: Session = Depends(get_db),
    params: PageParams = Depends(pagination_params),
    entity_type: str | None = Query(default=None),
    action: str | None = Query(default=None),
    _: User = Depends(require_reviewer),
) -> Page[AuditLogRead]:
    return AuditService(db).list_logs(
        params, filters={"entity_type": entity_type, "action": action}
    )


@router.get(
    "/version-history/{entity_type}/{entity_id}",
    response_model=list[VersionHistoryRead],
    dependencies=[Depends(require_reviewer)],
)
def list_version_history(
    entity_type: str,
    entity_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_reviewer),
) -> list[VersionHistoryRead]:
    return AuditService(db).list_versions(entity_type, entity_id)

"""ExpertSession schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from app.core.constants import ExpertSessionStatus
from app.schemas.common import AuditFieldsSchema, ORMBase


class ExpertSessionCreate(ORMBase):
    expert_id: uuid.UUID
    questionnaire_id: uuid.UUID
    scheduled_at: datetime | None = None
    summary: str | None = None


class ExpertSessionUpdate(ORMBase):
    status: ExpertSessionStatus | None = None
    scheduled_at: datetime | None = None
    completed_at: datetime | None = None
    summary: str | None = None


class ExpertSessionRead(AuditFieldsSchema):
    expert_id: uuid.UUID
    questionnaire_id: uuid.UUID
    status: ExpertSessionStatus
    scheduled_at: datetime | None = None
    completed_at: datetime | None = None
    summary: str | None = None

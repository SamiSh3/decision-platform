"""Case schemas."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import Field

from app.core.constants import CaseStatus
from app.schemas.common import AuditFieldsSchema, ORMBase


class CaseCreate(ORMBase):
    domain_id: uuid.UUID
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    subject_data: dict[str, Any] = Field(default_factory=dict)


class CaseUpdate(ORMBase):
    title: str | None = None
    description: str | None = None
    status: CaseStatus | None = None
    subject_data: dict[str, Any] | None = None


class CaseRead(AuditFieldsSchema):
    domain_id: uuid.UUID
    title: str
    description: str | None = None
    status: CaseStatus
    subject_data: dict[str, Any]
    owner_id: uuid.UUID

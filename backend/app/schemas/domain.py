"""Domain schemas."""

from __future__ import annotations

from pydantic import Field

from app.schemas.common import AuditFieldsSchema, ORMBase


class DomainCreate(ORMBase):
    code: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    is_active: bool = True


class DomainUpdate(ORMBase):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    is_active: bool | None = None


class DomainRead(AuditFieldsSchema):
    code: str
    name: str
    description: str | None = None
    is_active: bool

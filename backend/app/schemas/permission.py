"""Permission and RolePermission schemas."""

from __future__ import annotations

import uuid

from pydantic import Field

from app.schemas.common import AuditFieldsSchema, ORMBase


class PermissionCreate(ORMBase):
    code: str = Field(min_length=1, max_length=150)
    resource: str = Field(min_length=1, max_length=100)
    action: str = Field(min_length=1, max_length=50)
    description: str | None = None


class PermissionUpdate(ORMBase):
    description: str | None = None


class PermissionRead(AuditFieldsSchema):
    code: str
    resource: str
    action: str
    description: str | None = None


class RolePermissionCreate(ORMBase):
    role_id: uuid.UUID
    permission_id: uuid.UUID


class RolePermissionRead(AuditFieldsSchema):
    role_id: uuid.UUID
    permission_id: uuid.UUID
    permission: PermissionRead | None = None

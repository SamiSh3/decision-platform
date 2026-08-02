"""User and Role schemas."""

from __future__ import annotations

import uuid

from pydantic import EmailStr, Field

from app.core.constants import RoleName
from app.schemas.common import AuditFieldsSchema, ORMBase


class RoleRead(AuditFieldsSchema):
    name: str
    description: str | None = None


class UserCreate(ORMBase):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)
    role: RoleName = RoleName.USER
    is_active: bool = True


class UserUpdate(ORMBase):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    password: str | None = Field(default=None, min_length=8)
    role: RoleName | None = None
    is_active: bool | None = None


class UserRead(AuditFieldsSchema):
    email: str
    full_name: str
    is_active: bool
    is_superuser: bool
    role_id: uuid.UUID
    role: RoleRead | None = None

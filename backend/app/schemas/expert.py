"""Expert schemas."""

from __future__ import annotations

import uuid

from pydantic import Field

from app.schemas.common import AuditFieldsSchema, ORMBase
from app.schemas.user import UserRead


class ExpertCreate(ORMBase):
    user_id: uuid.UUID
    specialty: str = Field(min_length=1, max_length=255)
    years_experience: int = Field(ge=0, default=0)
    credentials: str | None = None
    weight: float = Field(default=1.0, ge=0, le=9.999)
    bio: str | None = None


class ExpertUpdate(ORMBase):
    specialty: str | None = Field(default=None, min_length=1, max_length=255)
    years_experience: int | None = Field(default=None, ge=0)
    credentials: str | None = None
    weight: float | None = Field(default=None, ge=0, le=9.999)
    bio: str | None = None


class ExpertRead(AuditFieldsSchema):
    user_id: uuid.UUID
    specialty: str
    years_experience: int
    credentials: str | None = None
    weight: float
    bio: str | None = None
    user: UserRead | None = None

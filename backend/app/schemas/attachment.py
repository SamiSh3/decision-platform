"""Attachment schemas."""

from __future__ import annotations

import uuid

from pydantic import Field

from app.schemas.common import AuditFieldsSchema, ORMBase


class AttachmentCreate(ORMBase):
    entity_type: str = Field(min_length=1, max_length=50)
    entity_id: uuid.UUID
    file_name: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=150)
    size_bytes: int = Field(ge=0, default=0)
    storage_path: str = Field(min_length=1, max_length=1024)
    checksum: str | None = None


class AttachmentRead(AuditFieldsSchema):
    entity_type: str
    entity_id: uuid.UUID
    file_name: str
    content_type: str
    size_bytes: int
    storage_path: str
    checksum: str | None = None

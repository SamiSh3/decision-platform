"""Evidence and KnowledgeSource schemas."""

from __future__ import annotations

import uuid

from pydantic import Field

from app.schemas.common import AuditFieldsSchema, ORMBase


class KnowledgeSourceCreate(ORMBase):
    name: str = Field(min_length=1, max_length=255)
    source_type: str = Field(min_length=1, max_length=100)
    url: str | None = None
    publisher: str | None = None
    reliability_score: float = Field(default=0.8, ge=0, le=1)
    description: str | None = None


class KnowledgeSourceUpdate(ORMBase):
    name: str | None = None
    source_type: str | None = None
    url: str | None = None
    publisher: str | None = None
    reliability_score: float | None = Field(default=None, ge=0, le=1)
    description: str | None = None


class KnowledgeSourceRead(AuditFieldsSchema):
    name: str
    source_type: str
    url: str | None = None
    publisher: str | None = None
    reliability_score: float
    description: str | None = None


class EvidenceCreate(ORMBase):
    response_id: uuid.UUID
    knowledge_source_id: uuid.UUID | None = None
    description: str = Field(min_length=1)
    reliability_score: float = Field(default=0.8, ge=0, le=1)


class EvidenceUpdate(ORMBase):
    description: str | None = None
    reliability_score: float | None = Field(default=None, ge=0, le=1)
    knowledge_source_id: uuid.UUID | None = None


class EvidenceRead(AuditFieldsSchema):
    response_id: uuid.UUID
    knowledge_source_id: uuid.UUID | None = None
    description: str
    reliability_score: float

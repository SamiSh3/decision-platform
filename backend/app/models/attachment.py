"""Attachment model - polymorphic file attachments for cases, responses, evidence, etc."""

from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import BaseModel


class Attachment(BaseModel):
    __tablename__ = "attachments"

    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(150), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Attachment {self.file_name}>"

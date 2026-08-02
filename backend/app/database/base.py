"""Declarative base and reusable mixins for every model.

Every table in the platform includes: UUID primary key, created_at/updated_at,
created_by/updated_by, and a soft-delete flag, per the project's data-model
requirements.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, MetaData
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def utcnow() -> datetime:
    return datetime.now(UTC)


class UUIDPrimaryKeyMixin:
    """Adds a UUID primary key column."""

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    """Adds created_at / updated_at timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )


class AuditUserMixin:
    """Adds created_by / updated_by user references."""

    @staticmethod
    def _created_by_column() -> Mapped[uuid.UUID | None]:  # pragma: no cover
        raise NotImplementedError

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL", use_alter=True, name="fk_created_by_user"),
        nullable=True,
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL", use_alter=True, name="fk_updated_by_user"),
        nullable=True,
    )


class SoftDeleteMixin:
    """Adds a soft-delete flag and timestamp."""

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BaseModel(UUIDPrimaryKeyMixin, TimestampMixin, AuditUserMixin, SoftDeleteMixin, Base):
    """Abstract base class combining all standard mixins.

    Concrete models should inherit from this class to automatically receive:
    UUID primary key, created_at, updated_at, created_by, updated_by, is_deleted,
    deleted_at.
    """

    __abstract__ = True

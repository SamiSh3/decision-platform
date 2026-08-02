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
    """Adds created_by / updated_by user references.

    Constraint names are left to the shared naming convention (which incorporates
    the table name) rather than being hardcoded, since a fixed name reused across
    every model's FK would be ambiguous to Alembic's autogenerate diffing and can
    cause it to silently skip emitting the constraint for all but one table.

    `use_alter=True` is required here: `Role` (like every model) has
    `created_by`/`updated_by` pointing at `users.id`, while `User.role_id`
    points at `roles.id` - a genuine circular FK dependency between the two
    tables. `use_alter` tells SQLAlchemy/Alembic to defer these two columns'
    constraints to a follow-up `ALTER TABLE` after both tables exist, which is
    the standard way to break a two-table FK cycle.

    Caveat this cost us once already: Alembic's autogenerate only emits that
    follow-up `ALTER TABLE` automatically when it detects a FK added to an
    *existing* table. For a brand-new table created in the same migration,
    autogenerate embeds the `use_alter=True` FK inline in `create_table()` -
    where it is then silently dropped from the DDL rather than deferred, since
    nothing emits the separate `ALTER TABLE` for it. Any migration that adds a
    new model must include an explicit `op.create_foreign_key(...)` call for
    its `created_by`/`updated_by` columns; see
    `alembic/versions/8b92d956d709_*.py` for the pattern, and
    `docs/Database.md` for the full writeup.
    """

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL", use_alter=True),
        nullable=True,
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL", use_alter=True),
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

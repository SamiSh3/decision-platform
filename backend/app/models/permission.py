"""Permission model and the Role<->Permission association.

Permissions provide fine-grained, resource-scoped authorization ("cases:create",
"rules:publish") layered on top of coarse-grained role checks. A role is granted a
permission through a `RolePermission` row rather than a bare association table so
that grants themselves carry full audit fields (who granted it, when, soft-revoke).
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import Role


class Permission(BaseModel):
    """A single, atomic capability, e.g. 'cases:create' or 'rules:publish'."""

    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    resource: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    role_grants: Mapped[list[RolePermission]] = relationship(
        "RolePermission", back_populates="permission", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Permission {self.code}>"


class RolePermission(BaseModel):
    """Grants a Permission to a Role. Modeled as a first-class entity (rather than
    a bare secondary table) so grants themselves are auditable and soft-revocable."""

    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission_role_permission"),
    )

    role_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[Role] = relationship("Role", back_populates="permission_grants")
    permission: Mapped[Permission] = relationship("Permission", back_populates="role_grants")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<RolePermission role={self.role_id} permission={self.permission_id}>"

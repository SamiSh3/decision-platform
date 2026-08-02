"""User and Role models."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel

if TYPE_CHECKING:
    from app.models.expert import Expert
    from app.models.permission import RolePermission


class Role(BaseModel):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    users: Mapped[list[User]] = relationship(
        "User", back_populates="role", foreign_keys="[User.role_id]"
    )
    permission_grants: Mapped[list[RolePermission]] = relationship(
        "RolePermission", back_populates="role", cascade="all, delete-orphan"
    )

    @property
    def permission_codes(self) -> set[str]:
        """Codes of all non-deleted permissions granted to this role."""
        return {
            grant.permission.code
            for grant in self.permission_grants
            if not grant.is_deleted and not grant.permission.is_deleted
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Role {self.name}>"


class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    role_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False
    )
    role: Mapped[Role] = relationship("Role", back_populates="users", foreign_keys=[role_id])

    expert_profile: Mapped[Expert | None] = relationship(
        "Expert", back_populates="user", uselist=False, foreign_keys="Expert.user_id"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.email}>"

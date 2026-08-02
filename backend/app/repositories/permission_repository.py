"""Permission and RolePermission repositories."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.permission import Permission, RolePermission
from app.repositories.base import BaseRepository


class PermissionRepository(BaseRepository[Permission]):
    model = Permission

    def get_by_code(self, code: str) -> Permission | None:
        stmt = select(Permission).where(Permission.code == code, Permission.is_deleted.is_(False))
        return self.db.execute(stmt).scalar_one_or_none()


class RolePermissionRepository(BaseRepository[RolePermission]):
    model = RolePermission

    def get_grant(self, role_id: uuid.UUID, permission_id: uuid.UUID) -> RolePermission | None:
        stmt = select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
            RolePermission.is_deleted.is_(False),
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_role(self, role_id: uuid.UUID) -> list[RolePermission]:
        stmt = (
            select(RolePermission)
            .where(RolePermission.role_id == role_id, RolePermission.is_deleted.is_(False))
            .options(selectinload(RolePermission.permission))
        )
        return list(self.db.execute(stmt).scalars().all())

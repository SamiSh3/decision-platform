"""Permission service - manages the permission catalog and role grants."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.permission_repository import PermissionRepository, RolePermissionRepository
from app.repositories.user_repository import RoleRepository
from app.schemas.common import Page, PageParams
from app.schemas.permission import (
    PermissionCreate,
    PermissionRead,
    PermissionUpdate,
    RolePermissionCreate,
    RolePermissionRead,
)


class PermissionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = PermissionRepository(db)
        self.role_repo = RoleRepository(db)
        self.grant_repo = RolePermissionRepository(db)

    def create(self, payload: PermissionCreate, actor_id: uuid.UUID | None) -> PermissionRead:
        if self.repo.get_by_code(payload.code) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Permission code already exists"
            )
        instance = self.repo.create(payload.model_dump(), actor_id=actor_id)
        self.db.commit()
        return PermissionRead.model_validate(instance)

    def get(self, entity_id: uuid.UUID) -> PermissionRead:
        return PermissionRead.model_validate(self.repo.get_or_404(entity_id))

    def list_for_role(self, role_id: uuid.UUID) -> list[RolePermissionRead]:
        items = self.grant_repo.list_for_role(role_id)
        return [RolePermissionRead.model_validate(i) for i in items]

    def list(self, params: PageParams, filters: dict | None = None) -> Page[PermissionRead]:
        items, total = self.repo.list(
            filters=filters,
            page=params.page,
            page_size=params.page_size,
            sort_by=params.sort_by,
            sort_dir=params.sort_dir,
        )
        return Page.create(
            [PermissionRead.model_validate(i) for i in items], total, params.page, params.page_size
        )

    def update(
        self, entity_id: uuid.UUID, payload: PermissionUpdate, actor_id: uuid.UUID | None
    ) -> PermissionRead:
        instance = self.repo.get_or_404(entity_id)
        instance = self.repo.update(
            instance, payload.model_dump(exclude_unset=True), actor_id=actor_id
        )
        self.db.commit()
        return PermissionRead.model_validate(instance)

    def soft_delete(self, entity_id: uuid.UUID, actor_id: uuid.UUID | None) -> None:
        instance = self.repo.get_or_404(entity_id)
        self.repo.soft_delete(instance, actor_id=actor_id)
        self.db.commit()

    def grant_to_role(
        self, payload: RolePermissionCreate, actor_id: uuid.UUID | None
    ) -> RolePermissionRead:
        if self.role_repo.get(payload.role_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        if self.repo.get(payload.permission_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found"
            )
        existing = self.grant_repo.get_grant(payload.role_id, payload.permission_id)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Role already has this permission"
            )
        grant = self.grant_repo.create(payload.model_dump(), actor_id=actor_id)
        self.db.commit()
        refreshed = self.grant_repo.get(grant.id)
        return RolePermissionRead.model_validate(refreshed)

    def revoke_from_role(self, grant_id: uuid.UUID, actor_id: uuid.UUID | None) -> None:
        instance = self.grant_repo.get_or_404(grant_id)
        self.grant_repo.soft_delete(instance, actor_id=actor_id)
        self.db.commit()

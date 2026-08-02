"""Permission catalog and Role<->Permission grant endpoints (admin only)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_active_user, require_admin
from app.dependencies.pagination import pagination_params
from app.models.user import User
from app.schemas.common import Message, Page, PageParams
from app.schemas.permission import (
    PermissionCreate,
    PermissionRead,
    PermissionUpdate,
    RolePermissionCreate,
    RolePermissionRead,
)
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.post(
    "", response_model=PermissionRead, status_code=201, dependencies=[Depends(require_admin)]
)
def create_permission(
    payload: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> PermissionRead:
    return PermissionService(db).create(payload, actor_id=current_user.id)


@router.get("", response_model=Page[PermissionRead])
def list_permissions(
    db: Session = Depends(get_db),
    params: PageParams = Depends(pagination_params),
    resource: str | None = Query(default=None),
    _: User = Depends(get_current_active_user),
) -> Page[PermissionRead]:
    return PermissionService(db).list(params, filters={"resource": resource})


@router.get("/{permission_id}", response_model=PermissionRead)
def get_permission(
    permission_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> PermissionRead:
    return PermissionService(db).get(permission_id)


@router.patch(
    "/{permission_id}", response_model=PermissionRead, dependencies=[Depends(require_admin)]
)
def update_permission(
    permission_id: uuid.UUID,
    payload: PermissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> PermissionRead:
    return PermissionService(db).update(permission_id, payload, actor_id=current_user.id)


@router.delete("/{permission_id}", response_model=Message, dependencies=[Depends(require_admin)])
def delete_permission(
    permission_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Message:
    PermissionService(db).soft_delete(permission_id, actor_id=current_user.id)
    return Message(detail="Permission deleted")


@router.post(
    "/grants",
    response_model=RolePermissionRead,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
def grant_permission_to_role(
    payload: RolePermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> RolePermissionRead:
    return PermissionService(db).grant_to_role(payload, actor_id=current_user.id)


@router.delete("/grants/{grant_id}", response_model=Message, dependencies=[Depends(require_admin)])
def revoke_permission_from_role(
    grant_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_admin)
) -> Message:
    PermissionService(db).revoke_from_role(grant_id, actor_id=current_user.id)
    return Message(detail="Permission grant revoked")


@router.get("/roles/{role_id}/grants", response_model=list[RolePermissionRead])
def list_role_permissions(
    role_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_active_user)
) -> list[RolePermissionRead]:
    return PermissionService(db).list_for_role(role_id)

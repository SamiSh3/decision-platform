"""Rule (decision engine rule base) endpoints, including versioning."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.constants import RuleStatus
from app.database.session import get_db
from app.dependencies.auth import get_current_active_user, require_admin
from app.dependencies.pagination import pagination_params
from app.models.user import User
from app.schemas.common import Message, Page, PageParams
from app.schemas.rule import RuleCreate, RuleRead, RuleUpdate
from app.services.rule_service import RuleService

router = APIRouter(prefix="/rules", tags=["rules"])


@router.post("", response_model=RuleRead, status_code=201, dependencies=[Depends(require_admin)])
def create_rule(
    payload: RuleCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)
) -> RuleRead:
    return RuleService(db).create(payload, actor_id=current_user.id)


@router.get("", response_model=Page[RuleRead])
def list_rules(
    db: Session = Depends(get_db),
    params: PageParams = Depends(pagination_params),
    domain_id: uuid.UUID | None = Query(default=None),
    status_filter: RuleStatus | None = Query(default=None, alias="status"),
    _: User = Depends(get_current_active_user),
) -> Page[RuleRead]:
    return RuleService(db).list(params, filters={"domain_id": domain_id, "status": status_filter})


@router.get("/{rule_id}", response_model=RuleRead)
def get_rule(
    rule_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_active_user)
) -> RuleRead:
    return RuleService(db).get(rule_id)


@router.patch("/{rule_id}", response_model=RuleRead, dependencies=[Depends(require_admin)])
def update_rule(
    rule_id: uuid.UUID,
    payload: RuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> RuleRead:
    return RuleService(db).update(rule_id, payload, actor_id=current_user.id)


@router.post(
    "/{rule_id}/new-version",
    response_model=RuleRead,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
def create_new_rule_version(
    rule_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_admin)
) -> RuleRead:
    return RuleService(db).create_new_version(rule_id, actor_id=current_user.id)


@router.delete("/{rule_id}", response_model=Message, dependencies=[Depends(require_admin)])
def delete_rule(
    rule_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_admin)
) -> Message:
    RuleService(db).soft_delete(rule_id, actor_id=current_user.id)
    return Message(detail="Rule deleted")

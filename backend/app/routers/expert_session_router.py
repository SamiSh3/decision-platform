"""ExpertSession endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_active_user, require_expert
from app.dependencies.pagination import pagination_params
from app.models.user import User
from app.schemas.common import Message, Page, PageParams
from app.schemas.expert_session import (
    ExpertSessionCreate,
    ExpertSessionRead,
    ExpertSessionUpdate,
)
from app.services.expert_session_service import ExpertSessionService

router = APIRouter(prefix="/expert-sessions", tags=["expert-sessions"])


@router.post(
    "", response_model=ExpertSessionRead, status_code=201, dependencies=[Depends(require_expert)]
)
def create_session(
    payload: ExpertSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_expert),
) -> ExpertSessionRead:
    return ExpertSessionService(db).create(payload, actor_id=current_user.id)


@router.get("", response_model=Page[ExpertSessionRead])
def list_sessions(
    db: Session = Depends(get_db),
    params: PageParams = Depends(pagination_params),
    expert_id: uuid.UUID | None = Query(default=None),
    questionnaire_id: uuid.UUID | None = Query(default=None),
    _: User = Depends(get_current_active_user),
) -> Page[ExpertSessionRead]:
    return ExpertSessionService(db).list(
        params, filters={"expert_id": expert_id, "questionnaire_id": questionnaire_id}
    )


@router.get("/{session_id}", response_model=ExpertSessionRead)
def get_session(
    session_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_active_user)
) -> ExpertSessionRead:
    return ExpertSessionService(db).get(session_id)


@router.patch(
    "/{session_id}", response_model=ExpertSessionRead, dependencies=[Depends(require_expert)]
)
def update_session(
    session_id: uuid.UUID,
    payload: ExpertSessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_expert),
) -> ExpertSessionRead:
    return ExpertSessionService(db).update(session_id, payload, actor_id=current_user.id)


@router.delete("/{session_id}", response_model=Message, dependencies=[Depends(require_expert)])
def delete_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_expert),
) -> Message:
    ExpertSessionService(db).soft_delete(session_id, actor_id=current_user.id)
    return Message(detail="Expert session deleted")

"""Questionnaire and nested Question endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_active_user, require_admin
from app.dependencies.pagination import pagination_params
from app.models.user import User
from app.schemas.common import Message, Page, PageParams
from app.schemas.questionnaire import (
    QuestionCreate,
    QuestionnaireCreate,
    QuestionnaireRead,
    QuestionnaireUpdate,
    QuestionRead,
    QuestionUpdate,
)
from app.services.questionnaire_service import QuestionnaireService

router = APIRouter(prefix="/questionnaires", tags=["questionnaires"])


@router.post(
    "", response_model=QuestionnaireRead, status_code=201, dependencies=[Depends(require_admin)]
)
def create_questionnaire(
    payload: QuestionnaireCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> QuestionnaireRead:
    return QuestionnaireService(db).create(payload, actor_id=current_user.id)


@router.get("", response_model=Page[QuestionnaireRead])
def list_questionnaires(
    db: Session = Depends(get_db),
    params: PageParams = Depends(pagination_params),
    domain_id: uuid.UUID | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    _: User = Depends(get_current_active_user),
) -> Page[QuestionnaireRead]:
    return QuestionnaireService(db).list(
        params, filters={"domain_id": domain_id, "is_active": is_active}
    )


@router.get("/{questionnaire_id}", response_model=QuestionnaireRead)
def get_questionnaire(
    questionnaire_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> QuestionnaireRead:
    return QuestionnaireService(db).get(questionnaire_id)


@router.patch(
    "/{questionnaire_id}", response_model=QuestionnaireRead, dependencies=[Depends(require_admin)]
)
def update_questionnaire(
    questionnaire_id: uuid.UUID,
    payload: QuestionnaireUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> QuestionnaireRead:
    return QuestionnaireService(db).update(questionnaire_id, payload, actor_id=current_user.id)


@router.delete("/{questionnaire_id}", response_model=Message, dependencies=[Depends(require_admin)])
def delete_questionnaire(
    questionnaire_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Message:
    QuestionnaireService(db).soft_delete(questionnaire_id, actor_id=current_user.id)
    return Message(detail="Questionnaire deleted")


@router.post(
    "/{questionnaire_id}/new-version",
    response_model=QuestionnaireRead,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
def create_new_questionnaire_version(
    questionnaire_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> QuestionnaireRead:
    return QuestionnaireService(db).create_new_version(questionnaire_id, actor_id=current_user.id)


@router.post(
    "/{questionnaire_id}/questions",
    response_model=QuestionRead,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
def add_question(
    questionnaire_id: uuid.UUID,
    payload: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> QuestionRead:
    return QuestionnaireService(db).add_question(
        questionnaire_id, payload, actor_id=current_user.id
    )


@router.patch(
    "/{questionnaire_id}/questions/{question_id}",
    response_model=QuestionRead,
    dependencies=[Depends(require_admin)],
)
def update_question(
    questionnaire_id: uuid.UUID,
    question_id: uuid.UUID,
    payload: QuestionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> QuestionRead:
    return QuestionnaireService(db).update_question(question_id, payload, actor_id=current_user.id)

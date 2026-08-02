"""Response (expert answer) and Evidence endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_active_user, require_expert
from app.dependencies.pagination import pagination_params
from app.models.user import User
from app.schemas.common import Message, Page, PageParams
from app.schemas.evidence import EvidenceCreate, EvidenceRead, EvidenceUpdate
from app.schemas.response import ResponseCreate, ResponseRead, ResponseUpdate
from app.services.response_service import EvidenceService, ResponseService

router = APIRouter(tags=["responses"])


@router.post(
    "/responses",
    response_model=ResponseRead,
    status_code=201,
    dependencies=[Depends(require_expert)],
)
def create_response(
    payload: ResponseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_expert),
) -> ResponseRead:
    return ResponseService(db).create(payload, actor_id=current_user.id)


@router.get("/responses", response_model=Page[ResponseRead])
def list_responses(
    db: Session = Depends(get_db),
    params: PageParams = Depends(pagination_params),
    case_id: uuid.UUID | None = Query(default=None),
    question_id: uuid.UUID | None = Query(default=None),
    expert_id: uuid.UUID | None = Query(default=None),
    _: User = Depends(get_current_active_user),
) -> Page[ResponseRead]:
    return ResponseService(db).list(
        params, filters={"case_id": case_id, "question_id": question_id, "expert_id": expert_id}
    )


@router.get("/cases/{case_id}/responses", response_model=list[ResponseRead])
def list_responses_for_case(
    case_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_active_user)
) -> list[ResponseRead]:
    return ResponseService(db).list_for_case(case_id)


@router.get("/responses/{response_id}", response_model=ResponseRead)
def get_response(
    response_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> ResponseRead:
    return ResponseService(db).get(response_id)


@router.patch(
    "/responses/{response_id}", response_model=ResponseRead, dependencies=[Depends(require_expert)]
)
def update_response(
    response_id: uuid.UUID,
    payload: ResponseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_expert),
) -> ResponseRead:
    return ResponseService(db).update(response_id, payload, actor_id=current_user.id)


@router.delete(
    "/responses/{response_id}", response_model=Message, dependencies=[Depends(require_expert)]
)
def delete_response(
    response_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_expert),
) -> Message:
    ResponseService(db).soft_delete(response_id, actor_id=current_user.id)
    return Message(detail="Response deleted")


@router.post(
    "/evidence",
    response_model=EvidenceRead,
    status_code=201,
    dependencies=[Depends(require_expert)],
)
def create_evidence(
    payload: EvidenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_expert),
) -> EvidenceRead:
    return EvidenceService(db).create(payload, actor_id=current_user.id)


@router.get("/evidence", response_model=Page[EvidenceRead])
def list_evidence(
    db: Session = Depends(get_db),
    params: PageParams = Depends(pagination_params),
    response_id: uuid.UUID | None = Query(default=None),
    _: User = Depends(get_current_active_user),
) -> Page[EvidenceRead]:
    return EvidenceService(db).list(params, filters={"response_id": response_id})


@router.get("/evidence/{evidence_id}", response_model=EvidenceRead)
def get_evidence(
    evidence_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> EvidenceRead:
    return EvidenceService(db).get(evidence_id)


@router.patch(
    "/evidence/{evidence_id}", response_model=EvidenceRead, dependencies=[Depends(require_expert)]
)
def update_evidence(
    evidence_id: uuid.UUID,
    payload: EvidenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_expert),
) -> EvidenceRead:
    return EvidenceService(db).update(evidence_id, payload, actor_id=current_user.id)


@router.delete(
    "/evidence/{evidence_id}", response_model=Message, dependencies=[Depends(require_expert)]
)
def delete_evidence(
    evidence_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_expert),
) -> Message:
    EvidenceService(db).soft_delete(evidence_id, actor_id=current_user.id)
    return Message(detail="Evidence deleted")

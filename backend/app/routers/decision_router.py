"""Decision engine endpoints - evaluate a case and read back explainable results."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.schemas.decision import ConfidenceScoreRead, DecisionResultRead
from app.services.decision_service import DecisionService

router = APIRouter(tags=["decisions"])


@router.post("/cases/{case_id}/evaluate", response_model=DecisionResultRead, status_code=201)
def evaluate_case(
    case_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DecisionResultRead:
    return DecisionService(db).evaluate(case_id, actor_id=current_user.id)


@router.get("/cases/{case_id}/decision-results", response_model=list[DecisionResultRead])
def list_decision_results(
    case_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_active_user)
) -> list[DecisionResultRead]:
    return DecisionService(db).list_for_case(case_id)


@router.get("/cases/{case_id}/decision-results/latest", response_model=DecisionResultRead | None)
def get_latest_decision_result(
    case_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_active_user)
) -> DecisionResultRead | None:
    return DecisionService(db).get_latest_for_case(case_id)


@router.get("/decision-results/{result_id}", response_model=DecisionResultRead)
def get_decision_result(
    result_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_active_user)
) -> DecisionResultRead:
    return DecisionService(db).get(result_id)


@router.get("/cases/{case_id}/confidence-scores", response_model=list[ConfidenceScoreRead])
def list_confidence_scores(
    case_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_active_user)
) -> list[ConfidenceScoreRead]:
    return DecisionService(db).list_confidence_scores_for_case(case_id)

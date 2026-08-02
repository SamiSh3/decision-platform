"""Authentication endpoints: login, refresh, register, current user."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    service = AuthService(db)
    return service.login(payload.email, payload.password)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    service = AuthService(db)
    return service.refresh_access_token(payload.refresh_token)


@router.post("/register", response_model=UserRead, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> UserRead:
    service = AuthService(db)
    user = service.register(payload)
    return UserRead.model_validate(user)


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_active_user)) -> UserRead:
    return UserRead.model_validate(current_user)

"""Authentication service - login, token issuance/refresh, registration."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.constants import RoleName
from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import RoleRepository, UserRepository
from app.schemas.auth import RegisterRequest, TokenResponse


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.role_repo = RoleRepository(db)

    def authenticate(self, email: str, password: str) -> User:
        user = self.user_repo.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
            )
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
        return user

    def issue_tokens(self, user: User) -> TokenResponse:
        role_name = user.role.name if user.role else RoleName.USER.value
        access = create_access_token(str(user.id), role_name)
        refresh = create_refresh_token(str(user.id))
        return TokenResponse(access_token=access, refresh_token=refresh)

    def login(self, email: str, password: str) -> TokenResponse:
        user = self.authenticate(email, password)
        return self.issue_tokens(user)

    def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            ) from exc

        if payload.type != TokenType.REFRESH.value:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )

        user = self.user_repo.get(uuid.UUID(payload.sub))
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer valid"
            )
        return self.issue_tokens(user)

    def register(self, payload: RegisterRequest) -> User:
        existing = self.user_repo.get_by_email(payload.email)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="A user with this email already exists"
            )
        role = self.role_repo.get_by_name(RoleName.USER.value)
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Default role not configured; run the seed script",
            )
        user = self.user_repo.create(
            {
                "email": payload.email,
                "hashed_password": hash_password(payload.password),
                "full_name": payload.full_name,
                "role_id": role.id,
                "is_active": True,
            }
        )
        self.db.commit()
        self.db.refresh(user)
        return user

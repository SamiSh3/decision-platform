"""Authentication and RBAC dependencies for FastAPI routes."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.constants import RoleName
from app.core.security import TokenType, decode_token
from app.database.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None:
        raise credentials_exception
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise credentials_exception from exc

    if payload.type != TokenType.ACCESS.value:
        raise credentials_exception

    repo = UserRepository(db)
    try:
        import uuid

        user = repo.get(uuid.UUID(payload.sub))
    except (ValueError, TypeError) as exc:
        raise credentials_exception from exc

    if user is None or not user.is_active:
        raise credentials_exception
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user


def require_roles(*allowed_roles: RoleName) -> Callable[..., User]:
    """Dependency factory enforcing Role Based Access Control on a route."""

    def _checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.is_superuser:
            return current_user
        role_name = current_user.role.name if current_user.role else None
        allowed_names = {r.value for r in allowed_roles}
        if role_name not in allowed_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return _checker


def get_client_ip(request: Request) -> str | None:
    if request.client:
        return request.client.host
    return None


require_admin = require_roles(RoleName.ADMIN)
require_expert = require_roles(RoleName.ADMIN, RoleName.EXPERT)
require_reviewer = require_roles(RoleName.ADMIN, RoleName.REVIEWER)
require_any_staff = require_roles(RoleName.ADMIN, RoleName.EXPERT, RoleName.REVIEWER)

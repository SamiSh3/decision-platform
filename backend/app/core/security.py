"""Password hashing and JWT token utilities."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _create_token(
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type.value,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str, role: str, extra_claims: dict[str, Any] | None = None) -> str:
    claims = {"role": role}
    if extra_claims:
        claims.update(extra_claims)
    return _create_token(
        subject,
        TokenType.ACCESS,
        timedelta(minutes=settings.access_token_expire_minutes),
        claims,
    )


def create_refresh_token(subject: str) -> str:
    return _create_token(
        subject,
        TokenType.REFRESH,
        timedelta(days=settings.refresh_token_expire_days),
    )


class TokenPayload:
    def __init__(self, sub: str, type: str, jti: str, role: str | None = None) -> None:
        self.sub = sub
        self.type = type
        self.jti = jti
        self.role = role


def decode_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:  # pragma: no cover - defensive
        raise ValueError("Could not validate token") from exc
    return TokenPayload(
        sub=payload["sub"],
        type=payload["type"],
        jti=payload["jti"],
        role=payload.get("role"),
    )

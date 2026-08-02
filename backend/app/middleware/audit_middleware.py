"""Binds request-scoped context (request id, client IP) for audit logging via
structlog contextvars, so any log emitted during request handling carries it."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class AuditContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            client_ip=request.client.host if request.client else None,
            path=request.url.path,
            method=request.method,
        )
        try:
            return await call_next(request)
        finally:
            structlog.contextvars.clear_contextvars()

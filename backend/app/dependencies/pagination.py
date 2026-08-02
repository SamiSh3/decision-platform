"""Pagination query-parameter dependency."""

from __future__ import annotations

from fastapi import Query

from app.core.config import settings
from app.schemas.common import PageParams


def pagination_params(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=settings.default_page_size, ge=1, le=settings.max_page_size),
    sort_by: str | None = Query(default=None),
    sort_dir: str = Query(default="asc", pattern="^(asc|desc)$"),
) -> PageParams:
    return PageParams(page=page, page_size=page_size, sort_by=sort_by, sort_dir=sort_dir)

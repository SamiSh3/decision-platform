"""Shared Pydantic schemas: pagination envelope, base config, common mixins."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from app.utils.pagination import compute_total_pages

T = TypeVar("T")


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AuditFieldsSchema(ORMBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None
    is_deleted: bool = False


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: str | None = None
    sort_dir: str = Field(default="asc", pattern="^(asc|desc)$")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def create(cls, items: list[T], total: int, page: int, page_size: int) -> Page[T]:
        pages = compute_total_pages(total, page_size)
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class Message(BaseModel):
    detail: str

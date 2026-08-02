"""Generic repository providing CRUD, filtering, pagination and sorting for any model
built on `BaseModel`. Concrete repositories subclass this to add domain-specific
queries while reusing the common data-access plumbing."""

from __future__ import annotations

import uuid
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, asc, desc, func, select
from sqlalchemy.orm import InstrumentedAttribute, Session

from app.database.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """Base repository implementing the Repository Pattern over a SQLAlchemy session."""

    model: type[ModelType]

    def __init__(self, db: Session) -> None:
        self.db = db

    def _base_query(self, include_deleted: bool = False) -> Select[Any]:
        stmt = select(self.model)
        if not include_deleted:
            stmt = stmt.where(self.model.is_deleted.is_(False))
        return stmt

    def get(self, entity_id: uuid.UUID, include_deleted: bool = False) -> ModelType | None:
        stmt = self._base_query(include_deleted).where(self.model.id == entity_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_or_404(self, entity_id: uuid.UUID) -> ModelType:
        from fastapi import HTTPException, status

        instance = self.get(entity_id)
        if instance is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__name__} with id {entity_id} not found",
            )
        return instance

    def list(
        self,
        *,
        filters: dict[str, Any] | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str | None = None,
        sort_dir: str = "asc",
        include_deleted: bool = False,
    ) -> tuple[list[ModelType], int]:
        stmt = self._base_query(include_deleted)
        stmt = self._apply_filters(stmt, filters or {})

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        if sort_by and hasattr(self.model, sort_by):
            column: InstrumentedAttribute[Any] = getattr(self.model, sort_by)
            stmt = stmt.order_by(desc(column) if sort_dir == "desc" else asc(column))
        else:
            stmt = stmt.order_by(desc(self.model.created_at))

        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        items = list(self.db.execute(stmt).scalars().all())
        return items, total

    def _apply_filters(self, stmt: Select[Any], filters: dict[str, Any]) -> Select[Any]:
        for key, value in filters.items():
            if value is None:
                continue
            if not hasattr(self.model, key):
                continue
            column = getattr(self.model, key)
            if isinstance(value, str):
                stmt = stmt.where(column.ilike(f"%{value}%"))
            else:
                stmt = stmt.where(column == value)
        return stmt

    def create(self, obj_in: dict[str, Any], actor_id: uuid.UUID | None = None) -> ModelType:
        data = dict(obj_in)
        if actor_id is not None:
            data.setdefault("created_by", actor_id)
            data.setdefault("updated_by", actor_id)
        instance = self.model(**data)
        self.db.add(instance)
        self.db.flush()
        self.db.refresh(instance)
        return instance

    def update(
        self, instance: ModelType, obj_in: dict[str, Any], actor_id: uuid.UUID | None = None
    ) -> ModelType:
        for key, value in obj_in.items():
            if value is not None and hasattr(instance, key):
                setattr(instance, key, value)
        if actor_id is not None:
            instance.updated_by = actor_id
        self.db.add(instance)
        self.db.flush()
        self.db.refresh(instance)
        return instance

    def soft_delete(self, instance: ModelType, actor_id: uuid.UUID | None = None) -> ModelType:
        from app.database.base import utcnow

        instance.is_deleted = True
        instance.deleted_at = utcnow()
        if actor_id is not None:
            instance.updated_by = actor_id
        self.db.add(instance)
        self.db.flush()
        self.db.refresh(instance)
        return instance

    def restore(self, instance: ModelType, actor_id: uuid.UUID | None = None) -> ModelType:
        instance.is_deleted = False
        instance.deleted_at = None
        if actor_id is not None:
            instance.updated_by = actor_id
        self.db.add(instance)
        self.db.flush()
        self.db.refresh(instance)
        return instance

    def hard_delete(self, instance: ModelType) -> None:
        self.db.delete(instance)
        self.db.flush()

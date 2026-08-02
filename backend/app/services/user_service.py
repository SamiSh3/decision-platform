"""User service - business logic for user management."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.repositories.user_repository import RoleRepository, UserRepository
from app.schemas.common import Page, PageParams
from app.schemas.user import UserCreate, UserRead, UserUpdate


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = UserRepository(db)
        self.role_repo = RoleRepository(db)

    def create(self, payload: UserCreate, actor_id: uuid.UUID | None) -> UserRead:
        if self.repo.get_by_email(payload.email) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
            )
        role = self.role_repo.get_by_name(payload.role.value)
        if role is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown role")
        user = self.repo.create(
            {
                "email": payload.email,
                "hashed_password": hash_password(payload.password),
                "full_name": payload.full_name,
                "role_id": role.id,
                "is_active": payload.is_active,
            },
            actor_id=actor_id,
        )
        self.db.commit()
        return UserRead.model_validate(user)

    def get(self, entity_id: uuid.UUID) -> UserRead:
        return UserRead.model_validate(self.repo.get_or_404(entity_id))

    def list(self, params: PageParams, filters: dict | None = None) -> Page[UserRead]:
        items, total = self.repo.list(
            filters=filters,
            page=params.page,
            page_size=params.page_size,
            sort_by=params.sort_by,
            sort_dir=params.sort_dir,
        )
        return Page.create(
            [UserRead.model_validate(i) for i in items], total, params.page, params.page_size
        )

    def update(
        self, entity_id: uuid.UUID, payload: UserUpdate, actor_id: uuid.UUID | None
    ) -> UserRead:
        instance = self.repo.get_or_404(entity_id)
        data = payload.model_dump(exclude_unset=True, exclude={"role", "password"})
        if payload.password:
            data["hashed_password"] = hash_password(payload.password)
        if payload.role:
            role = self.role_repo.get_by_name(payload.role.value)
            if role is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown role")
            data["role_id"] = role.id
        instance = self.repo.update(instance, data, actor_id=actor_id)
        self.db.commit()
        return UserRead.model_validate(instance)

    def soft_delete(self, entity_id: uuid.UUID, actor_id: uuid.UUID | None) -> None:
        instance = self.repo.get_or_404(entity_id)
        self.repo.soft_delete(instance, actor_id=actor_id)
        self.db.commit()

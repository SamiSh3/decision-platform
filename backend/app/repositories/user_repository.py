"""User and Role repositories."""

from __future__ import annotations

from sqlalchemy import select

from app.models.user import Role, User
from app.repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    model = Role

    def get_by_name(self, name: str) -> Role | None:
        stmt = select(Role).where(Role.name == name, Role.is_deleted.is_(False))
        return self.db.execute(stmt).scalar_one_or_none()


class UserRepository(BaseRepository[User]):
    model = User

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email, User.is_deleted.is_(False))
        return self.db.execute(stmt).scalar_one_or_none()

"""Shared pytest fixtures.

Tests run against a real PostgreSQL database (JSONB/ARRAY/UUID columns are not
portable to SQLite). Each test runs inside a SAVEPOINT that is rolled back
afterwards, so tests are isolated without needing to recreate the schema per test.

Set TEST_DATABASE_URL to point at a disposable PostgreSQL database before running
the suite; it defaults to a local Postgres instance matching docker-compose.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://decision_user:decision_password@localhost:5432/decision_platform_test",
    ),
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from app.core.constants import RoleName  # noqa: E402
from app.core.security import create_access_token, hash_password  # noqa: E402
from app.database.base import Base  # noqa: E402
from app.database.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import Role, User  # noqa: E402

engine = create_engine(TEST_DATABASE_URL, future=True)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@pytest.fixture(scope="session", autouse=True)
def _create_schema() -> Generator[None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session() -> Generator[Session]:
    from sqlalchemy import event

    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess: Session, trans: object) -> None:
        if trans.nested and not trans._parent.nested:  # type: ignore[attr-defined]
            sess.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient]:
    def _get_test_db() -> Generator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def roles(db_session: Session) -> dict[str, Role]:
    result = {}
    for role_name in RoleName:
        role = Role(name=role_name.value, description=f"{role_name.value} role")
        db_session.add(role)
        db_session.flush()
        result[role_name.value] = role
    db_session.commit()
    return result


def _make_user(
    db_session: Session, roles: dict[str, Role], role_name: RoleName, email: str
) -> User:
    user = User(
        email=email,
        hashed_password=hash_password("Password123!"),
        full_name=f"Test {role_name.value.title()}",
        role_id=roles[role_name.value].id,
        is_active=True,
        is_superuser=(role_name == RoleName.ADMIN),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session: Session, roles: dict[str, Role]) -> User:
    return _make_user(
        db_session, roles, RoleName.ADMIN, f"admin-{uuid.uuid4().hex[:8]}@test.example"
    )


@pytest.fixture
def expert_user(db_session: Session, roles: dict[str, Role]) -> User:
    return _make_user(
        db_session, roles, RoleName.EXPERT, f"expert-{uuid.uuid4().hex[:8]}@test.example"
    )


@pytest.fixture
def reviewer_user(db_session: Session, roles: dict[str, Role]) -> User:
    return _make_user(
        db_session, roles, RoleName.REVIEWER, f"reviewer-{uuid.uuid4().hex[:8]}@test.example"
    )


@pytest.fixture
def plain_user(db_session: Session, roles: dict[str, Role]) -> User:
    return _make_user(db_session, roles, RoleName.USER, f"user-{uuid.uuid4().hex[:8]}@test.example")


def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(str(user.id), user.role.name)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(admin_user: User) -> dict[str, str]:
    return auth_headers(admin_user)


@pytest.fixture
def expert_headers(expert_user: User) -> dict[str, str]:
    return auth_headers(expert_user)


@pytest.fixture
def user_headers(plain_user: User) -> dict[str, str]:
    return auth_headers(plain_user)


@pytest.fixture
def reviewer_headers(reviewer_user: User) -> dict[str, str]:
    return auth_headers(reviewer_user)

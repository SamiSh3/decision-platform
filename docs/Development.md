# Development

## Prerequisites

- Python 3.13
- Docker + Docker Compose (recommended), or a local PostgreSQL 16 instance

## Quick start (Docker)

```bash
cp .env.example .env
docker compose up --build
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed.py
```

API: http://localhost:8000, Swagger: http://localhost:8000/docs.

## Local development (no Docker)

```bash
python3 -m venv .venv && source .venv/bin/activate
make install            # pip install -r requirements-dev.txt + pre-commit install
cp .env.example .env    # edit DATABASE_URL to point at your local Postgres
make migrate            # alembic upgrade head
make seed                # scripts/seed.py
make run                 # uvicorn --reload on :8000
```

## Makefile targets

| Target | Description |
|---|---|
| `make install` | Install dev dependencies + pre-commit hooks |
| `make run` | Run the API with `--reload` |
| `make migrate` | Apply all pending Alembic migrations |
| `make makemigrations m="message"` | Autogenerate a new migration |
| `make seed` | Populate roles, permissions, users, the used-car domain, and sample data |
| `make test` | Run pytest with coverage |
| `make lint` | `ruff check backend` |
| `make format` | `black backend` + `ruff check --fix backend` |
| `make typecheck` | `mypy backend` |
| `make precommit` | Run all pre-commit hooks against the whole tree |
| `make up` / `make down` | Docker Compose up/down |

## Running tests

Tests run against a real PostgreSQL database (JSONB/ARRAY/UUID columns aren't
portable to SQLite). Point `TEST_DATABASE_URL` at a disposable database:

```bash
createdb decision_platform_test   # or: psql -c "CREATE DATABASE decision_platform_test;"
export TEST_DATABASE_URL="postgresql+psycopg://decision_user:decision_password@localhost:5432/decision_platform_test"
make test
```

`backend/tests/conftest.py` creates the full schema once per test session and
wraps each individual test in a `SAVEPOINT` that's rolled back afterwards, so
tests are isolated without paying the cost of recreating the schema per test.
A `db_session` fixture gives direct ORM access for engine-level unit tests;
a `client` fixture gives a `TestClient` wired to that same session via
dependency override, for full HTTP-level tests.

## Code quality gates

Every commit should pass all four before being pushed:

```bash
black --check backend
ruff check backend
mypy backend
pytest
```

`pre-commit` runs the first three (plus trailing-whitespace/EOF/yaml checks)
automatically on `git commit` once `make install` has run
`pre-commit install`.

## Adding a new domain

See the "Extending to a new domain" section of
[DecisionEngine.md](./DecisionEngine.md) - it's entirely data-driven via the
existing CRUD endpoints (`/domains`, `/questionnaires`, `/rules`, ...), no
code changes required.

## Adding a new entity/endpoint

1. Model in `backend/app/models/<entity>.py`, extending `BaseModel`; register
   it in `backend/app/models/__init__.py`.
2. Generate a migration: `make makemigrations m="add <entity>"`, review the
   generated file, then `make migrate`.
3. Schemas in `backend/app/schemas/<entity>.py` (`*Create`, `*Update`,
   `*Read`, extending `ORMBase`/`AuditFieldsSchema` from `schemas/common.py`).
4. Repository in `backend/app/repositories/<entity>_repository.py`,
   extending `BaseRepository[Model]` - only add methods for queries the
   generic CRUD/filter/paginate/sort doesn't cover.
5. Service in `backend/app/services/<entity>_service.py` - business rules,
   existence/uniqueness checks, and the only place that calls `db.commit()`.
6. Router in `backend/app/routers/<entity>_router.py` - thin HTTP layer,
   wraps the service, applies `Depends(require_roles(...))` /
   `Depends(require_permissions(...))` as needed.
7. Register the router in `backend/app/main.py`.
8. Tests in `backend/tests/test_<entity>.py`.

## Style

- Line length 100 (`black`, `ruff` both configured for it in `pyproject.toml`).
- `from __future__ import annotations` at the top of every module so `X | None`
  and generic builtins (`list[X]`, `dict[str, X]`) work without imports and
  forward references resolve automatically.
- Type-annotate everything meaningful; `mypy` runs in the CI pipeline and
  should report zero errors.

# Decision Platform

A Decision Intelligence Platform that captures expert knowledge through structured
questionnaires and converts it into a reusable knowledge repository and a rule-based
decision engine.

The first implemented domain is **Used Car Purchase Decision**. The platform is built
domain-driven so new domains (Real Estate, Medical Decisions, Insurance, Investment,
Procurement) can be added by seeding new `Domain`, `Questionnaire`, `Question` and `Rule`
records — no code changes required for the core engine.

## Architecture

Clean Architecture / Domain-Driven Design, feature-based layout:

```
backend/app/
  api/            # API-wide exception handlers, OpenAPI customization
  core/           # config, security, logging, constants
  database/       # SQLAlchemy engine/session, base class
  models/         # SQLAlchemy ORM models (one module per aggregate)
  schemas/        # Pydantic v2 request/response schemas
  repositories/   # Repository pattern - data access, no business logic
  services/       # Service layer - business logic, orchestration
  routers/        # FastAPI routers (HTTP layer only)
  dependencies/   # FastAPI dependency-injection providers
  middleware/     # Request logging, audit context
  knowledge/       # Knowledge capture domain logic
  decision_engine/ # Rule matching / confidence scoring / recommendation engine
```

## Tech stack

Python 3.13, FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL, Pydantic v2, Docker,
Docker Compose, Pytest, Ruff, Black, Mypy, pre-commit, JWT auth with refresh tokens, RBAC.

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

The API will be available at http://localhost:8000, Swagger UI at
http://localhost:8000/docs, ReDoc at http://localhost:8000/redoc.

Run migrations and seed sample data (car-purchase domain):

```bash
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed.py
```

Default seeded users (password for all: `Password123!`):

| email                     | role     |
|---------------------------|----------|
| admin@decision-platform.example      | admin    |
| expert@decision-platform.example     | expert   |
| reviewer@decision-platform.example   | reviewer |
| user@decision-platform.example       | user     |

## Local development (without Docker)

```bash
make install
make migrate
make seed
make run
```

## Tests

```bash
make test
```

## Makefile targets

See `Makefile` for `install`, `run`, `migrate`, `makemigrations`, `seed`, `test`,
`lint`, `format`, `typecheck`, `precommit`.

## Decision engine overview

1. Experts answer `Questionnaire` `Question`s for a `Case` producing `Response`s, each
   carrying confidence, reasoning, evidence, conditions, exceptions, importance, risk,
   notes and references (`knowledge` package).
2. `Rule`s are versioned domain objects made of `RuleCondition`s (matched against
   responses/attributes) and `RuleOutcome`s (weighted recommendation contributions).
3. The `decision_engine` package matches applicable rules for a case, aggregates
   outcomes across possibly conflicting expert opinions using expert-weighted
   confidence scoring, and produces a `DecisionResult` with a full, structured
   explanation trace.

## Documentation

- [docs/Architecture.md](docs/Architecture.md) - layering, request flow, auth model
- [docs/API.md](docs/API.md) - endpoint reference and conventions
- [docs/Database.md](docs/Database.md) - entity list, relationships, migrations
- [docs/Development.md](docs/Development.md) - setup, Makefile targets, testing, adding entities
- [docs/DecisionEngine.md](docs/DecisionEngine.md) - rule engine pipeline in depth

## License

Proprietary - internal reference implementation.

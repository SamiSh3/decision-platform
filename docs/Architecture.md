# Architecture

## Overview

Decision Platform is a domain-driven Decision Intelligence Platform. The core
engine — knowledge capture, rule evaluation, expert-weighted confidence
scoring — is deliberately domain-agnostic. Domain-specific content (which
questions to ask, which rules to apply) lives entirely in data (`Domain`,
`Questionnaire`, `Question`, `Rule` rows), not in code. Adding a new domain
(Real Estate, Medical Decisions, Insurance, Investment, Procurement) means
seeding new rows, not writing new endpoints or engine logic.

## Layering (Clean Architecture)

```
backend/app/
  api/              API-wide concerns: exception handlers, OpenAPI customization
  core/
    config/         Settings (env-driven), split into its own subpackage
    security.py     Password hashing, JWT encode/decode
    logging.py      structlog configuration
    constants.py    Domain-wide enums (roles, question types, rule operators, ...)
  database/         SQLAlchemy engine/session, declarative Base + audit/soft-delete mixins
  models/           SQLAlchemy ORM models - one module per aggregate
  schemas/          Pydantic v2 request/response DTOs
  repositories/      Repository Pattern - data access only, no business rules
  services/         Business logic and orchestration; the only layer allowed to commit()
  decision_engine/  Rule matching, expert-opinion aggregation, scoring, explanation
  knowledge/        Knowledge-capture quality heuristics (reasoning/evidence validation)
  routers/          FastAPI routers - HTTP concerns only, delegate to services
  dependencies/     FastAPI DI providers: current user, RBAC guards, pagination params
  middleware/       Request logging, audit request-context binding
  utils/            Small, dependency-free pure functions shared across layers
```

Dependency direction is strictly inward: `routers` depend on `services`, which
depend on `repositories`, which depend on `models`/`database`. Nothing in
`models`, `repositories`, or `decision_engine` imports from `routers` or
`schemas`. `schemas` are pure DTOs with no database awareness.

## Request flow

```
HTTP request
  -> router (validates via Pydantic schema, resolves DI: db session, current user, RBAC)
  -> service (business rules: existence checks, conflict checks, orchestration)
  -> repository (SQL via SQLAlchemy Core/ORM, filtering/pagination/sorting)
  -> model (ORM row) <-> PostgreSQL
  <- service maps ORM row(s) to a response schema
  <- router returns the schema; FastAPI serializes to JSON
```

Services are the only layer that calls `db.commit()`. Repositories `flush()`
so callers can read back generated values (IDs, defaults) inside the same
transaction, but never commit — that keeps multi-step operations (e.g.
creating a Rule plus its Conditions and Outcomes) atomic.

## Authentication & Authorization

- **Authentication**: JWT access tokens (short-lived) + refresh tokens
  (longer-lived), issued by `AuthService`. Tokens carry `sub` (user id), `type`
  (`access`/`refresh`), and for access tokens, the user's role name.
- **Coarse authorization (RBAC)**: `require_roles(*roles)` in
  `dependencies/auth.py` — a FastAPI dependency factory used as
  `Depends(require_admin)`, `Depends(require_expert)`, etc.
- **Fine-grained authorization**: `require_permissions(*codes)` checks the
  current user's role against `Permission`/`RolePermission` grants (e.g.
  `"rules:publish"`). It composes with `require_roles` rather than replacing
  it — an endpoint can require a role AND a specific permission.
- Superusers (`User.is_superuser`) bypass both checks.

## The Decision Engine

See [DecisionEngine.md](./DecisionEngine.md) for the full design. In brief:
`DecisionEngine.evaluate_case()` loads a Case's expert Responses and a
Domain's active Rules, aggregates potentially conflicting expert opinions
per question (`ExpertOpinionAggregator`), matches Rule conditions against
that aggregated view plus the Case's raw subject data (`RuleMatcher`),
computes a weighted overall score, maps it to a `RecommendationLabel`, and
persists a fully explainable `DecisionResult` plus per-rule `ConfidenceScore`
rows.

## Data model

See [Database.md](./Database.md) for the full entity list and relationships.
Every table shares a common set of mixins (`app/database/base.py`):
UUID primary key, `created_at`/`updated_at`, `created_by`/`updated_by` (FK to
`users.id`), and `is_deleted`/`deleted_at` for soft delete. A shared
`naming_convention` on the metadata ensures every constraint gets a unique,
predictable name (`fk_<table>_<column>_<referred_table>`, `uq_<table>_<col>`,
etc.) — this matters for Alembic autogenerate correctness, see the note in
`Database.md` about the FK-naming bug this convention was introduced to fix.

## Observability

Structured JSON logging via `structlog` (`core/logging.py`), bound with
per-request context (`X-Request-ID`, client IP, path, method) by
`middleware/logging_middleware.py` and `middleware/audit_middleware.py`.
Every response carries an `X-Request-ID` header for correlating logs.

## Error handling

Centralized in `api/exception_handlers.py`: `HTTPException` (validation/business
errors), `RequestValidationError` (422 with structured field errors),
`IntegrityError` (409 for DB constraint violations), generic `SQLAlchemyError`
and unhandled `Exception` (500, logged with full context, generic message
returned to the client).

# API

Interactive docs: Swagger UI at `/docs`, ReDoc at `/redoc`, raw OpenAPI schema
at `/openapi.json`. Everything below is a summary; the live schema is the
source of truth.

Base path: `/api/v1`. All endpoints (except `/health`, `/auth/login`,
`/auth/register`, `/auth/refresh`) require a Bearer access token.

## Conventions

- **Pagination**: list endpoints accept `page` (default 1), `page_size`
  (default 20, max 100), `sort_by` (any column name on the entity), and
  `sort_dir` (`asc`/`desc`). Responses are wrapped:
  `{"items": [...], "total": N, "page": N, "page_size": N, "pages": N}`.
- **Filtering**: list endpoints expose entity-appropriate query params (e.g.
  `GET /cases?domain_id=...&status=in_progress`). String filters use
  case-insensitive partial match (`ILIKE`); others use exact match.
- **Soft delete**: `DELETE` endpoints soft-delete (set `is_deleted=true`,
  `deleted_at=now()`); deleted rows are excluded from all reads by default.
- **Errors**: `{"detail": "...", "path": "..."}` for most errors;
  `{"detail": "Validation error", "errors": [...], "path": "..."}` for 422s.
- **HTTP codes**: `200` (read/update/delete), `201` (create), `401`
  (missing/invalid token), `403` (authenticated but not authorized), `404`
  (not found), `409` (conflict, e.g. duplicate unique field), `422`
  (validation error), `500` (unexpected server error).

## Authentication

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | none | Create a `user`-role account |
| POST | `/auth/login` | none | Returns `{access_token, refresh_token, token_type}` |
| POST | `/auth/refresh` | none | Exchange a refresh token for a new access token |
| GET  | `/auth/me` | any | Current authenticated user |

## Users & RBAC

| Method | Path | Auth | Description |
|---|---|---|---|
| POST/GET/PATCH/DELETE | `/users`, `/users/{id}` | admin (read: any) | User CRUD |
| POST/GET/PATCH/DELETE | `/permissions`, `/permissions/{id}` | admin (read: any) | Permission catalog CRUD |
| POST | `/permissions/grants` | admin | Grant a permission to a role |
| DELETE | `/permissions/grants/{id}` | admin | Revoke a grant |
| GET | `/permissions/roles/{role_id}/grants` | any | List a role's active grants |

## Knowledge capture

| Method | Path | Auth | Description |
|---|---|---|---|
| POST/GET/PATCH/DELETE | `/experts`, `/experts/{id}` | admin write, any read | Expert profiles |
| POST/GET/PATCH/DELETE | `/domains`, `/domains/{id}` | admin write, any read | Decision domains |
| POST/GET/PATCH/DELETE | `/questionnaires`, `/questionnaires/{id}` | admin write, any read | Questionnaires |
| POST/PATCH | `/questionnaires/{id}/questions[/{qid}]` | admin | Add/update questions |
| POST/GET/PATCH/DELETE | `/responses`, `/responses/{id}` | expert write, any read | Expert answers |
| GET | `/cases/{id}/responses` | any | All responses for a case |
| POST/GET/PATCH/DELETE | `/evidence`, `/evidence/{id}` | expert write, any read | Supporting evidence |
| POST/GET/PATCH/DELETE | `/knowledge-sources`, `/knowledge-sources/{id}` | expert write, any read | Citable sources |
| POST/GET/PATCH/DELETE | `/expert-sessions`, `/expert-sessions/{id}` | expert write, any read | Capture sessions |

## Cases & decisions

| Method | Path | Auth | Description |
|---|---|---|---|
| POST/GET/PATCH/DELETE | `/cases`, `/cases/{id}` | any authenticated | Case CRUD |
| POST | `/cases/{id}/evaluate` | any | Run the decision engine, returns a `DecisionResult` |
| GET | `/cases/{id}/decision-results` | any | All decision results for a case |
| GET | `/cases/{id}/decision-results/latest` | any | Most recent decision result |
| GET | `/decision-results/{id}` | any | A single decision result |
| GET | `/decision-results/{id}/explanation` | any | Plain-text rendered explanation |
| GET | `/cases/{id}/confidence-scores` | any | Per-rule confidence scores for a case |

## Rules

| Method | Path | Auth | Description |
|---|---|---|---|
| POST/GET/PATCH/DELETE | `/rules`, `/rules/{id}` | admin write, any read | Rule CRUD (with nested conditions/outcomes on create) |
| POST | `/rules/{id}/new-version` | admin | Fork an immutable new draft version |

## Attachments & audit

| Method | Path | Auth | Description |
|---|---|---|---|
| POST/GET/DELETE | `/attachments`, `/attachments/{id}` | any authenticated | File metadata |
| GET | `/attachments/by-entity/{type}/{id}` | any | Attachments for any entity |
| GET | `/audit-logs` | reviewer/admin | Audit trail |
| GET | `/version-history/{entity_type}/{entity_id}` | reviewer/admin | Version snapshots |

## Health

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | none | `{"status": "ok", "app": ..., "env": ...}` |

## Example: end-to-end flow

```bash
# 1. Log in
TOKEN=$(curl -s -X POST localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@decision-platform.example","password":"Password123!"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# 2. List seeded cases
curl -s localhost:8000/api/v1/cases -H "Authorization: Bearer $TOKEN"

# 3. Run the decision engine on one
curl -s -X POST localhost:8000/api/v1/cases/<CASE_ID>/evaluate \
  -H "Authorization: Bearer $TOKEN"

# 4. Read a human-readable explanation
curl -s localhost:8000/api/v1/decision-results/<RESULT_ID>/explanation \
  -H "Authorization: Bearer $TOKEN"
```

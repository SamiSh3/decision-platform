# Database

PostgreSQL 16, accessed via SQLAlchemy 2.x (declarative, typed `Mapped[...]`
columns) and versioned with Alembic. See `alembic/versions/` for the migration
history and `backend/app/models/` for the source of truth.

## Shared conventions

Every table inherits from `app.database.base.BaseModel`, which composes:

| Mixin              | Columns                                  | Purpose                          |
|---------------------|-------------------------------------------|-----------------------------------|
| `UUIDPrimaryKeyMixin`| `id` (UUID, default `uuid4()`)            | Primary key                       |
| `TimestampMixin`     | `created_at`, `updated_at`                | Row lifecycle timestamps          |
| `AuditUserMixin`     | `created_by`, `updated_by` (FK -> users.id)| Who created/last touched the row  |
| `SoftDeleteMixin`    | `is_deleted`, `deleted_at`                 | Soft delete instead of DELETE     |

A shared `naming_convention` on `Base.metadata` generates predictable,
**unique** constraint names, e.g. `fk_cases_created_by_users`,
`uq_rule_domain_code_version`. This matters in practice: an earlier revision
of this project hardcoded a single shared constraint name
(`fk_created_by_user`) for the `created_by` FK on every table. Because that
name collided across all 20+ models, Alembic's autogenerate diffing treated
it as "already seen" and silently skipped emitting the constraint for every
table but one - the audit FKs were present in the ORM layer but missing from
the actual database. Switching to the naming-convention-derived name (which
incorporates the table name) fixed this; see migration
`8b92d956d709_add_permissions_role_permissions_and_.py` for the backfill.

## Entities

| Entity | Purpose |
|---|---|
| `User` | Login identity, one `Role` |
| `Role` | Coarse RBAC role (admin/expert/reviewer/user) |
| `Permission` | Fine-grained capability code (`resource:action`) |
| `RolePermission` | Grants a `Permission` to a `Role`; itself soft-revocable |
| `Expert` | Domain-expert profile for a `User`; carries a decision-engine trust `weight` |
| `Domain` | Top-level decision domain (e.g. `used_car_purchase`) |
| `Questionnaire` | Versioned set of `Question`s for a `Domain` |
| `Question` | A single question; typed (`single_choice`/`numeric`/`boolean`/...) |
| `QuestionOption` | Selectable option for choice-type questions |
| `Case` | One concrete decision instance (e.g. one specific car purchase) |
| `Response` | An expert's answer to a `Question` for a `Case` - carries confidence, reasoning, conditions, exceptions, importance, risk, notes, references |
| `Evidence` | Supporting evidence attached to a `Response` |
| `KnowledgeSource` | A reusable, citable source (manual, standard, article, experience) |
| `Rule` | A versioned rule in a `Domain`'s rule base |
| `RuleCondition` | One condition of a `Rule` (attribute path + operator + value + OR-group id) |
| `RuleOutcome` | The recommendation contribution a `Rule` produces when it fires |
| `ConfidenceScore` | Per-case, per-rule computed confidence + explainability trace |
| `DecisionResult` | Final recommendation + full explanation JSON for a `Case` |
| `ExpertSession` | A scheduled/completed knowledge-capture session with an `Expert` |
| `Attachment` | Polymorphic file metadata (`entity_type` + `entity_id`) |
| `AuditLog` | Immutable record of significant actions |
| `VersionHistory` | Snapshot storage for versioned entities (`Questionnaire`, `Rule`) |

## Key relationships

```
Domain 1---* Questionnaire 1---* Question 1---* QuestionOption
Domain 1---* Rule 1---* RuleCondition
                  Rule 1---* RuleOutcome
Domain 1---* Case 1---* Response *---1 Question
                  Case 1---* Response *---1 Expert
                  Response 1---* Evidence *---1 KnowledgeSource (optional)
                  Case 1---* ConfidenceScore *---1 Rule
                  Case 1---* DecisionResult
User 1---1 Expert
User *---1 Role *---* Permission  (through RolePermission)
```

## Rule condition attribute paths

`RuleCondition.attribute_path` uses one of two prefixes, resolved by
`decision_engine.matcher.resolve_attribute`:

- `question:<code>` - the aggregated expert answer for that question code
- `subject:<field>` - a field on `Case.subject_data` (arbitrary JSON supplied
  when the case was created, e.g. `{"year": 2019, "asking_price": 18500}`)

## Migrations

```bash
alembic revision --autogenerate -m "description"   # generate
alembic upgrade head                                # apply
alembic downgrade -1                                # roll back one
```

`alembic/env.py` imports `app.models` (which imports every model module) so
`Base.metadata` is fully populated before autogenerate diffs against it -
this is required for autogenerate to see every table.

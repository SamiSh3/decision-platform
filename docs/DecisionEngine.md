# Decision Engine

`backend/app/decision_engine/` implements a reusable, domain-agnostic rule
engine. It never references "cars" or any other domain concept directly -
all domain knowledge lives in `Rule`/`RuleCondition`/`RuleOutcome` rows and
`Question`/`Response` data.

## Pipeline

`DecisionEngine.evaluate_case(case_id)` (`decision_engine/engine.py`) runs:

1. **Load** the `Case` (with `subject_data`), its `Response`s, and the
   `Domain`'s active `Rule`s (each with `conditions` and `outcomes`).
2. **Aggregate expert opinions** per question
   (`ExpertOpinionAggregator.aggregate`, `decision_engine/aggregator.py`):
   multiple experts may answer the same question differently. Each expert's
   contribution is weighted by `expert.weight * response.confidence`
   ("effective weight"). Numeric answers are combined via a weighted mean;
   categorical answers (choice/boolean/text) via weighted majority vote.
3. **Detect conflicts**: numeric answers conflict if the weighted
   coefficient of variation exceeds `NUMERIC_CONFLICT_CV_THRESHOLD` (0.25);
   categorical answers conflict if the winning value holds less than
   `AGREEMENT_THRESHOLD` (0.6) of total weight.
4. **Match rules** (`RuleMatcher.matches`, `decision_engine/matcher.py`):
   conditions are grouped by `group_id`; groups are OR'd together, conditions
   within a group are AND'd. A rule with zero conditions always matches
   (useful as a domain-wide default). Each condition resolves its
   `attribute_path` against either the aggregated answers (`question:<code>`)
   or the case's raw `subject_data` (`subject:<field>`), then evaluates the
   configured `RuleOperator` (`equals`, `greater_than`, `in`, `between`, ...).
5. **Score confidence per matched rule**: a rule's confidence is the average
   aggregated-answer confidence across every question its conditions
   reference (rules that only reference `subject_data` default to full
   confidence, since there's no expert opinion to be uncertain about). This
   is persisted as a `ConfidenceScore` row with a full calculation trace.
6. **Combine into an overall score**: for every outcome of every matched
   rule, `impact = outcome.score_impact * rule.weight * confidence.normalized_score`.
   The overall score is the weight-normalized sum of all impacts, clamped to
   `[-1, 1]`.
7. **Map to a recommendation** (`decision_engine/scoring.py`): threshold
   bands turn the `[-1, 1]` score into a `RecommendationLabel`
   (`strongly_recommended` down to `strongly_not_recommended`).
8. **Render explanations** (`decision_engine/explanation.py`): each
   `RuleOutcome.explanation_template` supports `{field}` placeholders filled
   from `subject_data` first, then aggregated answers, e.g.
   `"Mileage of {mileage} km is high"`.
9. **Persist** a `DecisionResult` with the recommendation, overall score,
   overall confidence, and a structured `explanation` JSON containing every
   matched rule (with its condition trace and rendered explanation) and
   every aggregated answer (with its full per-expert contribution trace).

## Weighted experts & conflicting opinions

Two independent weights combine multiplicatively:

- **`Expert.weight`** - a static trust weight configured per expert (e.g. a
  senior inspector might be weighted 1.5x a junior one).
- **`Response.confidence`** - how confident *that expert* is in *this specific
  answer* (0-1), captured at knowledge-entry time.

`effective_weight = expert.weight * response.confidence`. This means a
highly-trusted expert who is personally unsure about one particular answer
contributes less to that specific question than their default weight would
suggest - confidence is answer-specific, not a blanket multiplier on
everything that expert says.

When two experts disagree, both distributions are still visible in the
resulting `ConfidenceScore.calculation_trace` and the `DecisionResult`
explanation's `aggregated_answers[...].contributions` list - nothing is
silently discarded. The engine picks the weighted-majority answer but flags
`conflict_detected: true` wherever that majority is not decisive, so a human
reviewer can drill into exactly which experts disagreed and by how much.

## Rule versioning

Rules are versioned, not mutated in place. `RuleService.create_new_version()`
copies an existing rule's code/name/priority/weight plus all conditions and
outcomes into a **new** row with `version = old.version + 1` and
`status = draft`. The original rule is untouched and keeps its `active`
status until an operator explicitly promotes the new version (by setting its
status to `active` and, typically, deprecating the old one). Every version
creation is also recorded in `VersionHistory` for full audit trail.

Only rules with `status = active` are loaded by
`RuleRepository.list_active_for_domain()` and considered during evaluation -
draft and deprecated versions are inert until explicitly activated.

## Explainability by design

Every number the engine produces is traceable back to its inputs:

- `ConfidenceScore.calculation_trace` records the exact condition evaluations
  (attribute path, operator, expected value, actual resolved value, boolean
  result) for the rule that produced it.
- `DecisionResult.explanation.matched_rules[]` lists, per matched rule: its
  code/name/version, the outcome direction and score impact, the rule's
  weight, the resolved confidence, whether a conflict was detected, the
  rendered explanation text, and the full condition trace.
- `DecisionResult.explanation.aggregated_answers{}` lists, per question code:
  the aggregated value, aggregated confidence, conflict flag, and every
  individual expert's raw contribution (their weight, their stated
  confidence, their effective weight, and their answer).

`GET /api/v1/decision-results/{id}/explanation` renders this into
human-readable prose via `utils/explanation_formatter.py` for consumers that
want a summary rather than the raw JSON.

## Extending to a new domain

No engine code changes are required to add a new domain:

1. Create a `Domain` row (e.g. `code="real_estate"`).
2. Create a `Questionnaire` + `Question`s (+ `QuestionOption`s for choice
   questions) for that domain.
3. Create `Rule`s with `RuleCondition`s referencing those question codes
   (or the new domain's `Case.subject_data` shape) and `RuleOutcome`s with
   their own explanation templates.
4. Seed or capture `Expert` responses against real `Case`s in that domain.
5. Call `POST /cases/{id}/evaluate` - the same `DecisionEngine` code path
   handles it.

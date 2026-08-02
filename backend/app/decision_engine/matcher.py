"""Evaluates RuleConditions against a Case's subject data and aggregated expert
answers. Attribute paths use the convention:

    question:<question_code>   -> aggregated expert answer for that question
    subject:<field_name>       -> a field on Case.subject_data
"""

from __future__ import annotations

from typing import Any

from app.core.constants import RuleOperator
from app.decision_engine.aggregator import AggregatedAnswer
from app.models.rule import RuleCondition

QUESTION_PREFIX = "question:"
SUBJECT_PREFIX = "subject:"


class AttributeResolutionError(Exception):
    """Raised when a rule condition references an attribute with no available value."""


def resolve_attribute(
    attribute_path: str,
    subject_data: dict[str, Any],
    aggregated_answers: dict[str, AggregatedAnswer],
) -> Any:
    if attribute_path.startswith(QUESTION_PREFIX):
        code = attribute_path[len(QUESTION_PREFIX) :]
        aggregated = aggregated_answers.get(code)
        if aggregated is None:
            raise AttributeResolutionError(f"No expert answer available for question '{code}'")
        return aggregated.value
    if attribute_path.startswith(SUBJECT_PREFIX):
        field_name = attribute_path[len(SUBJECT_PREFIX) :]
        if field_name not in subject_data:
            raise AttributeResolutionError(f"Case subject data has no field '{field_name}'")
        return subject_data[field_name]
    raise AttributeResolutionError(
        f"Attribute path '{attribute_path}' must start with "
        f"'{QUESTION_PREFIX}' or '{SUBJECT_PREFIX}'"
    )


def _coerce_comparable(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def evaluate_operator(operator: RuleOperator, actual: Any, expected: Any) -> bool:
    if operator == RuleOperator.EQUALS:
        return actual == expected
    if operator == RuleOperator.NOT_EQUALS:
        return actual != expected
    if operator == RuleOperator.IN:
        return actual in expected
    if operator == RuleOperator.NOT_IN:
        return actual not in expected
    if operator == RuleOperator.CONTAINS:
        return expected in actual if actual is not None else False

    left = _coerce_comparable(actual)
    if operator == RuleOperator.BETWEEN:
        low, high = expected
        return _coerce_comparable(low) <= left <= _coerce_comparable(high)

    right = _coerce_comparable(expected)
    if operator == RuleOperator.GREATER_THAN:
        return left > right
    if operator == RuleOperator.GREATER_OR_EQUAL:
        return left >= right
    if operator == RuleOperator.LESS_THAN:
        return left < right
    if operator == RuleOperator.LESS_OR_EQUAL:
        return left <= right

    raise ValueError(f"Unsupported operator: {operator}")


class RuleMatcher:
    """Determines whether a Rule's conditions are satisfied for a given Case."""

    def matches(
        self,
        conditions: list[RuleCondition],
        subject_data: dict[str, Any],
        aggregated_answers: dict[str, AggregatedAnswer],
    ) -> tuple[bool, list[dict[str, Any]]]:
        """Conditions are grouped by `group_id`; groups are OR'd together, and
        conditions within a group are AND'd together. A rule with no conditions
        always matches (useful for domain-wide default/fallback rules)."""
        if not conditions:
            return True, []

        groups: dict[int, list[RuleCondition]] = {}
        for condition in conditions:
            groups.setdefault(condition.group_id, []).append(condition)

        trace: list[dict[str, Any]] = []
        any_group_matched = False

        for group_id, group_conditions in groups.items():
            group_matched = True
            for condition in group_conditions:
                entry: dict[str, Any] = {
                    "group_id": group_id,
                    "attribute_path": condition.attribute_path,
                    "operator": (
                        condition.operator.value
                        if hasattr(condition.operator, "value")
                        else condition.operator
                    ),
                    "expected": condition.value,
                }
                try:
                    actual = resolve_attribute(
                        condition.attribute_path, subject_data, aggregated_answers
                    )
                    result = evaluate_operator(condition.operator, actual, condition.value)
                except AttributeResolutionError as exc:
                    actual = None
                    result = False
                    entry["error"] = str(exc)
                entry["actual"] = actual
                entry["result"] = result
                trace.append(entry)
                group_matched = group_matched and result
            any_group_matched = any_group_matched or group_matched

        return any_group_matched, trace

"""Unit tests for the expert opinion aggregator and rule condition matcher,
independent of the database."""

from __future__ import annotations

import uuid
from types import SimpleNamespace

from app.core.constants import RuleOperator
from app.decision_engine.aggregator import ExpertOpinionAggregator
from app.decision_engine.matcher import RuleMatcher, evaluate_operator


def _fake_response(expert_id: uuid.UUID, value, confidence: float) -> SimpleNamespace:
    return SimpleNamespace(
        expert_id=expert_id, answer_value={"value": value}, confidence=confidence
    )


def _fake_expert(weight: float) -> SimpleNamespace:
    return SimpleNamespace(weight=weight)


def test_aggregator_numeric_weighted_mean() -> None:
    expert_1, expert_2 = uuid.uuid4(), uuid.uuid4()
    experts = {str(expert_1): _fake_expert(2.0), str(expert_2): _fake_expert(1.0)}
    responses = [
        _fake_response(expert_1, 100, 1.0),
        _fake_response(expert_2, 40, 1.0),
    ]
    aggregator = ExpertOpinionAggregator()
    result = aggregator.aggregate("mileage", responses, experts)
    assert result is not None
    # weighted mean: (100*2 + 40*1) / 3 = 80
    assert round(result.value, 2) == 80.0
    assert result.contributing_expert_count == 2


def test_aggregator_categorical_majority_no_conflict() -> None:
    expert_1, expert_2, expert_3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    experts = {
        str(expert_1): _fake_expert(1.0),
        str(expert_2): _fake_expert(1.0),
        str(expert_3): _fake_expert(1.0),
    }
    responses = [
        _fake_response(expert_1, "good", 1.0),
        _fake_response(expert_2, "good", 1.0),
        _fake_response(expert_3, "good", 1.0),
    ]
    aggregator = ExpertOpinionAggregator()
    result = aggregator.aggregate("engine_condition", responses, experts)
    assert result is not None
    assert result.value == "good"
    assert result.conflict_detected is False


def test_aggregator_categorical_split_opinion_is_conflict() -> None:
    expert_1, expert_2 = uuid.uuid4(), uuid.uuid4()
    experts = {str(expert_1): _fake_expert(1.0), str(expert_2): _fake_expert(1.0)}
    responses = [
        _fake_response(expert_1, "good", 1.0),
        _fake_response(expert_2, "poor", 1.0),
    ]
    aggregator = ExpertOpinionAggregator()
    result = aggregator.aggregate("engine_condition", responses, experts)
    assert result is not None
    assert result.conflict_detected is True


def test_evaluate_operator_numeric_and_membership() -> None:
    assert evaluate_operator(RuleOperator.GREATER_THAN, 100, 50) is True
    assert evaluate_operator(RuleOperator.LESS_OR_EQUAL, 50, 50) is True
    assert evaluate_operator(RuleOperator.IN, "good", ["good", "excellent"]) is True
    assert evaluate_operator(RuleOperator.NOT_IN, "poor", ["good", "excellent"]) is True
    assert evaluate_operator(RuleOperator.BETWEEN, 5, [1, 10]) is True
    assert evaluate_operator(RuleOperator.EQUALS, "a", "a") is True
    assert evaluate_operator(RuleOperator.NOT_EQUALS, "a", "b") is True


def test_rule_matcher_or_groups() -> None:
    condition_a = SimpleNamespace(
        attribute_path="subject:year", operator=RuleOperator.LESS_THAN, value=2015, group_id=0
    )
    condition_b = SimpleNamespace(
        attribute_path="subject:mileage",
        operator=RuleOperator.GREATER_THAN,
        value=100000,
        group_id=1,
    )
    matcher = RuleMatcher()
    matched, trace = matcher.matches(
        [condition_a, condition_b],
        subject_data={"year": 2020, "mileage": 150000},
        aggregated_answers={},
    )
    # group_id=0 fails (year not < 2015) but group_id=1 succeeds (mileage > 100000) -> OR match
    assert matched is True
    assert len(trace) == 2


def test_rule_matcher_no_conditions_always_matches() -> None:
    matcher = RuleMatcher()
    matched, trace = matcher.matches([], subject_data={}, aggregated_answers={})
    assert matched is True
    assert trace == []

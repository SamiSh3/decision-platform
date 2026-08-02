"""Tests for the rule-based decision engine: matching, expert-weighted confidence,
conflicting-opinion detection, and explainable recommendation generation."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.constants import (
    CaseStatus,
    OutcomeDirection,
    QuestionType,
    RuleOperator,
    RuleStatus,
)
from app.decision_engine.engine import DecisionEngine
from app.decision_engine.scoring import score_to_label
from app.models.case import Case
from app.models.domain import Domain
from app.models.expert import Expert
from app.models.question import Question
from app.models.questionnaire import Questionnaire
from app.models.response import Response
from app.models.rule import Rule, RuleCondition, RuleOutcome
from app.models.user import User


def _build_domain_with_question(db_session: Session) -> tuple[Domain, Questionnaire, Question]:
    domain = Domain(code="test_domain", name="Test Domain")
    db_session.add(domain)
    db_session.flush()

    questionnaire = Questionnaire(domain_id=domain.id, code="qq", title="Questionnaire")
    db_session.add(questionnaire)
    db_session.flush()

    question = Question(
        questionnaire_id=questionnaire.id,
        code="engine_condition",
        text="Engine condition?",
        question_type=QuestionType.SINGLE_CHOICE,
    )
    db_session.add(question)
    db_session.flush()
    return domain, questionnaire, question


def _make_expert(db_session: Session, roles, weight: float, email: str) -> Expert:
    from app.core.constants import RoleName
    from app.core.security import hash_password

    user = User(
        email=email,
        hashed_password=hash_password("Password123!"),
        full_name="Expert",
        role_id=roles[RoleName.EXPERT.value].id,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    expert = Expert(user_id=user.id, specialty="Testing", years_experience=5, weight=weight)
    db_session.add(expert)
    db_session.flush()
    return expert


def test_rule_matches_and_produces_recommended_decision(db_session: Session, roles) -> None:
    domain, questionnaire, question = _build_domain_with_question(db_session)
    expert = _make_expert(db_session, roles, weight=1.0, email="expert-a@test.example")

    owner = User(
        email="owner-a@test.example",
        hashed_password="x",
        full_name="Owner",
        role_id=roles["user"].id,
    )
    db_session.add(owner)
    db_session.flush()

    case = Case(
        domain_id=domain.id,
        title="Test case",
        status=CaseStatus.IN_PROGRESS,
        subject_data={},
        owner_id=owner.id,
    )
    db_session.add(case)
    db_session.flush()

    db_session.add(
        Response(
            case_id=case.id,
            question_id=question.id,
            expert_id=expert.id,
            answer_value={"value": "excellent"},
            confidence=0.9,
            reasoning="Engine runs perfectly with no issues detected during inspection.",
        )
    )

    rule = Rule(
        domain_id=domain.id,
        code="engine_good",
        name="Engine good",
        version=1,
        status=RuleStatus.ACTIVE,
        weight=1.0,
    )
    db_session.add(rule)
    db_session.flush()
    db_session.add(
        RuleCondition(
            rule_id=rule.id,
            attribute_path="question:engine_condition",
            operator=RuleOperator.EQUALS,
            value="excellent",
        )
    )
    db_session.add(
        RuleOutcome(
            rule_id=rule.id,
            direction=OutcomeDirection.BUY,
            score_impact=0.8,
            explanation_template="Engine condition is {engine_condition}.",
        )
    )
    db_session.commit()

    engine = DecisionEngine(db_session)
    result = engine.evaluate_case(case.id)

    assert result["overall_score"] > 0
    assert result["recommendation"] == score_to_label(result["overall_score"])
    assert result["explanation"]["rule_count_matched"] == 1
    assert (
        result["explanation"]["matched_rules"][0]["explanation"] == "Engine condition is excellent."
    )
    assert result["explanation"]["conflicts_detected"] is False


def test_conflicting_expert_opinions_are_detected(db_session: Session, roles) -> None:
    domain, questionnaire, question = _build_domain_with_question(db_session)
    expert_a = _make_expert(db_session, roles, weight=1.0, email="expert-b@test.example")
    expert_b = _make_expert(db_session, roles, weight=1.0, email="expert-c@test.example")

    owner = User(
        email="owner-b@test.example",
        hashed_password="x",
        full_name="Owner",
        role_id=roles["user"].id,
    )
    db_session.add(owner)
    db_session.flush()

    case = Case(
        domain_id=domain.id,
        title="Conflict case",
        status=CaseStatus.IN_PROGRESS,
        subject_data={},
        owner_id=owner.id,
    )
    db_session.add(case)
    db_session.flush()

    db_session.add(
        Response(
            case_id=case.id,
            question_id=question.id,
            expert_id=expert_a.id,
            answer_value={"value": "excellent"},
            confidence=0.9,
        )
    )
    db_session.add(
        Response(
            case_id=case.id,
            question_id=question.id,
            expert_id=expert_b.id,
            answer_value={"value": "poor"},
            confidence=0.9,
        )
    )

    rule = Rule(
        domain_id=domain.id,
        code="engine_good_conflict",
        name="Engine good",
        version=1,
        status=RuleStatus.ACTIVE,
        weight=1.0,
    )
    db_session.add(rule)
    db_session.flush()
    db_session.add(
        RuleCondition(
            rule_id=rule.id,
            attribute_path="question:engine_condition",
            operator=RuleOperator.EQUALS,
            value="excellent",
        )
    )
    db_session.add(
        RuleOutcome(
            rule_id=rule.id,
            direction=OutcomeDirection.BUY,
            score_impact=0.8,
            explanation_template="Engine condition is {engine_condition}.",
        )
    )
    db_session.commit()

    engine = DecisionEngine(db_session)
    result = engine.evaluate_case(case.id)

    aggregated = result["explanation"]["aggregated_answers"]["engine_condition"]
    assert aggregated["conflict_detected"] is True
    assert aggregated["contributing_expert_count"] == 2


def test_subject_data_only_rule_matches_without_expert_answers(db_session: Session, roles) -> None:
    domain = Domain(code="subject_only_domain", name="Subject Only")
    db_session.add(domain)
    db_session.flush()

    owner = User(
        email="owner-c@test.example",
        hashed_password="x",
        full_name="Owner",
        role_id=roles["user"].id,
    )
    db_session.add(owner)
    db_session.flush()

    case = Case(
        domain_id=domain.id,
        title="Subject-only case",
        status=CaseStatus.IN_PROGRESS,
        subject_data={"year": 2010},
        owner_id=owner.id,
    )
    db_session.add(case)
    db_session.flush()

    rule = Rule(
        domain_id=domain.id,
        code="old_vehicle",
        name="Old vehicle",
        version=1,
        status=RuleStatus.ACTIVE,
        weight=1.0,
    )
    db_session.add(rule)
    db_session.flush()
    db_session.add(
        RuleCondition(
            rule_id=rule.id,
            attribute_path="subject:year",
            operator=RuleOperator.LESS_THAN,
            value=2015,
        )
    )
    db_session.add(
        RuleOutcome(
            rule_id=rule.id,
            direction=OutcomeDirection.CAUTION,
            score_impact=-0.5,
            explanation_template="Vehicle year {year} is old.",
        )
    )
    db_session.commit()

    engine = DecisionEngine(db_session)
    result = engine.evaluate_case(case.id)

    assert result["explanation"]["rule_count_matched"] == 1
    assert result["explanation"]["matched_rules"][0]["explanation"] == "Vehicle year 2010 is old."
    assert result["overall_score"] < 0


def test_rule_with_unmatched_condition_does_not_fire(db_session: Session, roles) -> None:
    domain, questionnaire, question = _build_domain_with_question(db_session)
    expert = _make_expert(db_session, roles, weight=1.0, email="expert-d@test.example")

    owner = User(
        email="owner-d@test.example",
        hashed_password="x",
        full_name="Owner",
        role_id=roles["user"].id,
    )
    db_session.add(owner)
    db_session.flush()

    case = Case(
        domain_id=domain.id,
        title="No match case",
        status=CaseStatus.IN_PROGRESS,
        subject_data={},
        owner_id=owner.id,
    )
    db_session.add(case)
    db_session.flush()

    db_session.add(
        Response(
            case_id=case.id,
            question_id=question.id,
            expert_id=expert.id,
            answer_value={"value": "poor"},
            confidence=0.9,
        )
    )

    rule = Rule(
        domain_id=domain.id,
        code="engine_good_unmatched",
        name="Engine good",
        version=1,
        status=RuleStatus.ACTIVE,
        weight=1.0,
    )
    db_session.add(rule)
    db_session.flush()
    db_session.add(
        RuleCondition(
            rule_id=rule.id,
            attribute_path="question:engine_condition",
            operator=RuleOperator.EQUALS,
            value="excellent",
        )
    )
    db_session.add(
        RuleOutcome(
            rule_id=rule.id,
            direction=OutcomeDirection.BUY,
            score_impact=0.8,
            explanation_template="Engine condition is {engine_condition}.",
        )
    )
    db_session.commit()

    engine = DecisionEngine(db_session)
    result = engine.evaluate_case(case.id)

    assert result["explanation"]["rule_count_matched"] == 0
    assert result["overall_score"] == 0.0
    assert result["recommendation"] == score_to_label(0.0)

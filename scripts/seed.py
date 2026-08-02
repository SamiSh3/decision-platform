"""Seed script - populates roles, default users/experts, and the full
'Used Car Purchase Decision' domain: questionnaire, questions, options, a sample
case with expert responses, and a rule set for the decision engine.

Run with: python scripts/seed.py  (PYTHONPATH must include backend/, see Makefile)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.core.constants import (  # noqa: E402
    CaseStatus,
    ImportanceLevel,
    OutcomeDirection,
    QuestionType,
    RiskLevel,
    RoleName,
    RuleOperator,
    RuleStatus,
)
from app.core.security import hash_password  # noqa: E402
from app.database.session import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    Case,
    Domain,
    Evidence,
    Expert,
    KnowledgeSource,
    Question,
    Questionnaire,
    QuestionOption,
    Response,
    Role,
    Rule,
    RuleCondition,
    RuleOutcome,
    User,
)

DEFAULT_PASSWORD = "Password123!"


def get_or_create(session, model, defaults=None, **filters):
    instance = session.query(model).filter_by(**filters).first()
    if instance is not None:
        return instance, False
    params = dict(filters)
    params.update(defaults or {})
    instance = model(**params)
    session.add(instance)
    session.flush()
    return instance, True


def seed_roles(session) -> dict[str, Role]:
    roles = {}
    for role_name in RoleName:
        role, _ = get_or_create(
            session, Role, name=role_name.value, defaults={"description": f"{role_name.value} role"}
        )
        roles[role_name.value] = role
    return roles


def seed_users(session, roles: dict[str, Role]) -> dict[str, User]:
    users_spec = [
        ("admin@decision-platform.example", "Platform Admin", RoleName.ADMIN),
        ("expert@decision-platform.example", "Senior Vehicle Inspector", RoleName.EXPERT),
        ("reviewer@decision-platform.example", "Quality Reviewer", RoleName.REVIEWER),
        ("user@decision-platform.example", "Regular User", RoleName.USER),
    ]
    users = {}
    for email, full_name, role_name in users_spec:
        user, created = get_or_create(
            session,
            User,
            email=email,
            defaults={
                "hashed_password": hash_password(DEFAULT_PASSWORD),
                "full_name": full_name,
                "role_id": roles[role_name.value].id,
                "is_active": True,
                "is_superuser": role_name == RoleName.ADMIN,
            },
        )
        users[email] = user
    return users


def seed_expert(session, expert_user: User) -> Expert:
    expert, _ = get_or_create(
        session,
        Expert,
        user_id=expert_user.id,
        defaults={
            "specialty": "Used Vehicle Inspection & Valuation",
            "years_experience": 15,
            "credentials": "ASE Certified Master Technician",
            "weight": 1.5,
            "bio": "15 years inspecting used vehicles for private buyers and dealerships.",
        },
    )
    return expert


def seed_car_domain(session) -> Domain:
    domain, _ = get_or_create(
        session,
        Domain,
        code="used_car_purchase",
        defaults={
            "name": "Used Car Purchase Decision",
            "description": (
                "Decision support for buying a used car: mechanical condition, history, "
                "price fairness and risk factors."
            ),
            "is_active": True,
        },
    )
    return domain


def seed_questionnaire(session, domain: Domain) -> tuple[Questionnaire, dict[str, Question]]:
    questionnaire, _ = get_or_create(
        session,
        Questionnaire,
        domain_id=domain.id,
        code="used_car_inspection",
        version=1,
        defaults={
            "title": "Used Car Purchase Inspection Questionnaire",
            "description": (
                "Structured expert inspection covering mechanical, history and price factors."
            ),
            "is_active": True,
        },
    )

    questions_spec = [
        {
            "code": "mileage",
            "text": "What is the vehicle's odometer reading, in kilometers?",
            "question_type": QuestionType.NUMERIC,
            "display_order": 1,
            "default_importance": ImportanceLevel.HIGH,
            "default_risk": RiskLevel.MEDIUM,
            "options": [],
        },
        {
            "code": "accident_history",
            "text": "Does the vehicle have a recorded accident history?",
            "question_type": QuestionType.BOOLEAN,
            "display_order": 2,
            "default_importance": ImportanceLevel.MANDATORY,
            "default_risk": RiskLevel.HIGH,
            "options": [
                {"value": "true", "label": "Yes", "display_order": 1},
                {"value": "false", "label": "No", "display_order": 2},
            ],
        },
        {
            "code": "engine_condition",
            "text": "What is the assessed condition of the engine?",
            "question_type": QuestionType.SINGLE_CHOICE,
            "display_order": 3,
            "default_importance": ImportanceLevel.MANDATORY,
            "default_risk": RiskLevel.HIGH,
            "options": [
                {
                    "value": "excellent",
                    "label": "Excellent",
                    "display_order": 1,
                    "score_weight": 1.0,
                },
                {"value": "good", "label": "Good", "display_order": 2, "score_weight": 0.6},
                {"value": "fair", "label": "Fair", "display_order": 3, "score_weight": 0.2},
                {"value": "poor", "label": "Poor", "display_order": 4, "score_weight": -1.0},
            ],
        },
        {
            "code": "price_to_market_ratio",
            "text": "Asking price divided by fair market value (1.0 = fair market price).",
            "question_type": QuestionType.NUMERIC,
            "display_order": 4,
            "default_importance": ImportanceLevel.HIGH,
            "default_risk": RiskLevel.MEDIUM,
            "options": [],
        },
        {
            "code": "service_records_complete",
            "text": "Are complete, verifiable service records available?",
            "question_type": QuestionType.BOOLEAN,
            "display_order": 5,
            "default_importance": ImportanceLevel.MEDIUM,
            "default_risk": RiskLevel.LOW,
            "options": [
                {"value": "true", "label": "Yes", "display_order": 1},
                {"value": "false", "label": "No", "display_order": 2},
            ],
        },
    ]

    questions: dict[str, Question] = {}
    for spec in questions_spec:
        options_spec = spec.pop("options")
        question, created = get_or_create(
            session,
            Question,
            questionnaire_id=questionnaire.id,
            code=spec["code"],
            defaults=spec,
        )
        if created:
            for opt in options_spec:
                get_or_create(
                    session,
                    QuestionOption,
                    question_id=question.id,
                    value=opt["value"],
                    defaults={
                        "label": opt["label"],
                        "display_order": opt["display_order"],
                        "score_weight": opt.get("score_weight", 0.0),
                    },
                )
        questions[question.code] = question

    return questionnaire, questions


def seed_knowledge_source(session) -> KnowledgeSource:
    source, _ = get_or_create(
        session,
        KnowledgeSource,
        name="ASE Used Vehicle Inspection Standard",
        defaults={
            "source_type": "manual",
            "publisher": "National Institute for Automotive Service Excellence",
            "reliability_score": 0.95,
            "description": "Industry-standard checklist for pre-purchase used vehicle inspections.",
        },
    )
    return source


def seed_case(
    session, domain: Domain, owner: User, expert: Expert, questions: dict[str, Question], source
) -> Case:
    case, created = get_or_create(
        session,
        Case,
        domain_id=domain.id,
        title="2019 Sedan - Sample Purchase Evaluation",
        defaults={
            "description": "Sample case seeded for demonstration of the decision engine.",
            "status": CaseStatus.IN_PROGRESS,
            "subject_data": {
                "make": "Toyota",
                "model": "Camry",
                "year": 2019,
                "asking_price": 18500,
                "fair_market_value": 19000,
            },
            "owner_id": owner.id,
        },
    )
    if not created:
        return case

    answers = [
        (
            "mileage",
            {"value": 62000},
            0.95,
            "Odometer read directly and cross-checked against records.",
        ),
        (
            "accident_history",
            {"value": False},
            0.9,
            "No accident records found in vehicle history report.",
        ),
        (
            "engine_condition",
            {"value": "good"},
            0.85,
            "Engine runs smoothly, minor oil seepage noted but not concerning.",
        ),
        (
            "price_to_market_ratio",
            {"value": 0.97},
            1.0,
            "Asking price is 18500 against a fair market value of 19000.",
        ),
        (
            "service_records_complete",
            {"value": True},
            0.8,
            "Dealer provided full service history with matching mileage entries.",
        ),
    ]

    for code, value, confidence, reasoning in answers:
        response, r_created = get_or_create(
            session,
            Response,
            case_id=case.id,
            question_id=questions[code].id,
            expert_id=expert.id,
            defaults={
                "answer_value": value,
                "confidence": confidence,
                "reasoning": reasoning,
                "conditions": "Assessment based on a single in-person inspection.",
                "exceptions": None,
                "importance": questions[code].default_importance,
                "risk": questions[code].default_risk,
                "notes": "Collected during standard 90-minute pre-purchase inspection.",
                "references": ["ASE Used Vehicle Inspection Standard"],
            },
        )
        if r_created:
            session.flush()
            get_or_create(
                session,
                Evidence,
                response_id=response.id,
                knowledge_source_id=source.id,
                defaults={
                    "description": (
                        f"Inspection checklist entry supporting the '{code}' assessment."
                    ),
                    "reliability_score": 0.9,
                },
            )

    return case


def seed_rules(session, domain: Domain) -> None:
    rules_spec = [
        {
            "code": "high_mileage_caution",
            "name": "High mileage caution",
            "description": "Flags vehicles with mileage above a risk threshold.",
            "priority": 10,
            "weight": 1.0,
            "conditions": [
                {
                    "attribute_path": "question:mileage",
                    "operator": RuleOperator.GREATER_THAN,
                    "value": 150000,
                    "group_id": 0,
                }
            ],
            "outcomes": [
                {
                    "direction": OutcomeDirection.CAUTION,
                    "score_impact": -0.4,
                    "explanation_template": (
                        "Mileage of {mileage} km is high and increases the likelihood of "
                        "upcoming maintenance costs."
                    ),
                }
            ],
        },
        {
            "code": "accident_history_risk",
            "name": "Accident history risk",
            "description": "Penalizes vehicles with a recorded accident history.",
            "priority": 5,
            "weight": 1.3,
            "conditions": [
                {
                    "attribute_path": "question:accident_history",
                    "operator": RuleOperator.EQUALS,
                    "value": True,
                    "group_id": 0,
                }
            ],
            "outcomes": [
                {
                    "direction": OutcomeDirection.NEEDS_INSPECTION,
                    "score_impact": -0.6,
                    "explanation_template": (
                        "The vehicle has a recorded accident history; a specialized "
                        "structural inspection is recommended before proceeding."
                    ),
                }
            ],
        },
        {
            "code": "engine_condition_good_or_better",
            "name": "Engine condition acceptable",
            "description": "Rewards vehicles with a good or excellent engine assessment.",
            "priority": 20,
            "weight": 1.2,
            "conditions": [
                {
                    "attribute_path": "question:engine_condition",
                    "operator": RuleOperator.IN,
                    "value": ["good", "excellent"],
                    "group_id": 0,
                }
            ],
            "outcomes": [
                {
                    "direction": OutcomeDirection.BUY,
                    "score_impact": 0.5,
                    "explanation_template": "Engine condition was assessed as {engine_condition}.",
                }
            ],
        },
        {
            "code": "fair_price",
            "name": "Fair or below-market price",
            "description": "Rewards vehicles priced at or below fair market value.",
            "priority": 15,
            "weight": 1.0,
            "conditions": [
                {
                    "attribute_path": "question:price_to_market_ratio",
                    "operator": RuleOperator.LESS_OR_EQUAL,
                    "value": 1.0,
                    "group_id": 0,
                }
            ],
            "outcomes": [
                {
                    "direction": OutcomeDirection.BUY,
                    "score_impact": 0.3,
                    "explanation_template": (
                        "Asking price is at or below fair market value "
                        "(ratio {price_to_market_ratio})."
                    ),
                }
            ],
        },
        {
            "code": "overpriced",
            "name": "Overpriced relative to market",
            "description": "Penalizes vehicles priced significantly above fair market value.",
            "priority": 15,
            "weight": 1.0,
            "conditions": [
                {
                    "attribute_path": "question:price_to_market_ratio",
                    "operator": RuleOperator.GREATER_THAN,
                    "value": 1.1,
                    "group_id": 0,
                }
            ],
            "outcomes": [
                {
                    "direction": OutcomeDirection.NEGOTIATE,
                    "score_impact": -0.3,
                    "explanation_template": (
                        "Asking price is more than 10% above fair market value "
                        "(ratio {price_to_market_ratio}); negotiate before proceeding."
                    ),
                }
            ],
        },
        {
            "code": "missing_service_records",
            "name": "Missing service records",
            "description": "Flags cases with no verifiable service history.",
            "priority": 25,
            "weight": 0.8,
            "conditions": [
                {
                    "attribute_path": "question:service_records_complete",
                    "operator": RuleOperator.EQUALS,
                    "value": False,
                    "group_id": 0,
                }
            ],
            "outcomes": [
                {
                    "direction": OutcomeDirection.CAUTION,
                    "score_impact": -0.25,
                    "explanation_template": (
                        "No complete service records are available, making maintenance "
                        "history harder to verify."
                    ),
                }
            ],
        },
    ]

    for spec in rules_spec:
        conditions_spec = spec.pop("conditions")
        outcomes_spec = spec.pop("outcomes")
        rule, created = get_or_create(
            session,
            Rule,
            domain_id=domain.id,
            code=spec["code"],
            version=1,
            defaults={**spec, "status": RuleStatus.ACTIVE},
        )
        if created:
            for cond in conditions_spec:
                session.add(RuleCondition(rule_id=rule.id, **cond))
            for outcome in outcomes_spec:
                session.add(RuleOutcome(rule_id=rule.id, **outcome))


def main() -> None:
    session = SessionLocal()
    try:
        roles = seed_roles(session)
        users = seed_users(session, roles)
        expert = seed_expert(session, users["expert@decision-platform.example"])
        domain = seed_car_domain(session)
        _, questions = seed_questionnaire(session, domain)
        source = seed_knowledge_source(session)
        seed_case(
            session, domain, users["user@decision-platform.example"], expert, questions, source
        )
        seed_rules(session, domain)
        session.commit()
        print("Seed completed successfully.")
        print(f"Domain: {domain.code}")
        print(f"Users created/verified: {list(users.keys())}")
        print(f"Default password for all seeded users: {DEFAULT_PASSWORD}")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()

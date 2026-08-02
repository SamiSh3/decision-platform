"""DecisionEngine - orchestrates rule matching, expert-opinion aggregation, confidence
scoring and final recommendation generation with a full explanation trace."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.decision_engine import ENGINE_VERSION
from app.decision_engine.aggregator import AggregatedAnswer, ExpertOpinionAggregator
from app.decision_engine.explanation import render_template
from app.decision_engine.matcher import RuleMatcher
from app.decision_engine.scoring import score_to_label
from app.models.expert import Expert
from app.models.question import Question
from app.models.response import Response
from app.models.rule import Rule
from app.repositories.case_repository import CaseRepository
from app.repositories.decision_repository import ConfidenceScoreRepository, DecisionResultRepository
from app.repositories.expert_repository import ExpertRepository
from app.repositories.questionnaire_repository import QuestionRepository
from app.repositories.response_repository import ResponseRepository
from app.repositories.rule_repository import RuleRepository


class DecisionEngine:
    """Computes an explainable DecisionResult for a Case."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.case_repo = CaseRepository(db)
        self.response_repo = ResponseRepository(db)
        self.question_repo = QuestionRepository(db)
        self.expert_repo = ExpertRepository(db)
        self.rule_repo = RuleRepository(db)
        self.confidence_repo = ConfidenceScoreRepository(db)
        self.result_repo = DecisionResultRepository(db)
        self.aggregator = ExpertOpinionAggregator()
        self.matcher = RuleMatcher()

    def evaluate_case(
        self, case_id: uuid.UUID, actor_id: uuid.UUID | None = None
    ) -> dict[str, Any]:
        case = self.case_repo.get(case_id)
        if case is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

        responses = self.response_repo.list_for_case(case_id)
        rules = self.rule_repo.list_active_for_domain(case.domain_id)

        aggregated_answers = self._aggregate_all_answers(responses)

        matched_rules_explanations: list[dict[str, Any]] = []
        weighted_score_sum = 0.0
        weighted_weight_sum = 0.0
        weighted_confidence_sum = 0.0
        any_conflict = False

        for rule in rules:
            matched, condition_trace = self.matcher.matches(
                rule.conditions, case.subject_data, aggregated_answers
            )
            if not matched:
                continue

            rule_confidence, contributing_experts, rule_conflict = self._rule_confidence(
                rule, aggregated_answers
            )
            any_conflict = any_conflict or rule_conflict

            confidence_score = self.confidence_repo.create(
                {
                    "case_id": case.id,
                    "rule_id": rule.id,
                    "raw_score": rule_confidence,
                    "normalized_score": min(max(rule_confidence, 0.0), 1.0),
                    "contributing_expert_count": contributing_experts,
                    "conflict_detected": rule_conflict,
                    "calculation_trace": {"conditions": condition_trace},
                },
                actor_id=actor_id,
            )

            for outcome in rule.outcomes:
                normalized_confidence = float(confidence_score.normalized_score)
                impact = float(outcome.score_impact) * float(rule.weight) * normalized_confidence
                weighted_score_sum += impact
                weighted_weight_sum += float(rule.weight) * normalized_confidence
                weighted_confidence_sum += normalized_confidence * float(rule.weight)

                explanation_text = render_template(
                    outcome.explanation_template, case.subject_data, aggregated_answers
                )
                matched_rules_explanations.append(
                    {
                        "rule_id": str(rule.id),
                        "rule_code": rule.code,
                        "rule_name": rule.name,
                        "rule_version": rule.version,
                        "outcome_direction": (
                            outcome.direction.value
                            if hasattr(outcome.direction, "value")
                            else outcome.direction
                        ),
                        "score_impact": float(outcome.score_impact),
                        "rule_weight": float(rule.weight),
                        "confidence": normalized_confidence,
                        "conflict_detected": rule_conflict,
                        "explanation": explanation_text,
                        "condition_trace": condition_trace,
                    }
                )

        overall_score = (
            max(min(weighted_score_sum / weighted_weight_sum, 1.0), -1.0)
            if weighted_weight_sum
            else 0.0
        )
        overall_confidence = (
            min(weighted_confidence_sum / weighted_weight_sum, 1.0) if weighted_weight_sum else 0.0
        )
        recommendation = score_to_label(overall_score)

        explanation_payload = {
            "matched_rules": matched_rules_explanations,
            "aggregated_answers": {
                code: answer.to_trace() for code, answer in aggregated_answers.items()
            },
            "conflicts_detected": any_conflict,
            "rule_count_evaluated": len(rules),
            "rule_count_matched": len(matched_rules_explanations),
        }

        result = self.result_repo.create(
            {
                "case_id": case.id,
                "recommendation": recommendation,
                "overall_score": overall_score,
                "overall_confidence": overall_confidence,
                "explanation": explanation_payload,
                "engine_version": ENGINE_VERSION,
            },
            actor_id=actor_id,
        )
        self.db.commit()
        self.db.refresh(result)
        return {
            "id": result.id,
            "case_id": result.case_id,
            "recommendation": result.recommendation,
            "overall_score": float(result.overall_score),
            "overall_confidence": float(result.overall_confidence),
            "explanation": result.explanation,
            "engine_version": result.engine_version,
            "created_at": result.created_at,
            "updated_at": result.updated_at,
            "created_by": result.created_by,
            "updated_by": result.updated_by,
            "is_deleted": result.is_deleted,
        }

    def _aggregate_all_answers(self, responses: list[Response]) -> dict[str, AggregatedAnswer]:
        if not responses:
            return {}

        question_ids = {r.question_id for r in responses}
        questions_by_id: dict[uuid.UUID, Question] = {
            q.id: q for q in (self.question_repo.get(qid) for qid in question_ids) if q is not None
        }

        expert_ids = {r.expert_id for r in responses}
        experts_by_id: dict[str, Expert] = {
            str(eid): expert
            for eid in expert_ids
            if (expert := self.expert_repo.get(eid)) is not None
        }

        responses_by_question: dict[uuid.UUID, list[Response]] = {}
        for response in responses:
            responses_by_question.setdefault(response.question_id, []).append(response)

        aggregated: dict[str, AggregatedAnswer] = {}
        for question_id, question_responses in responses_by_question.items():
            question = questions_by_id.get(question_id)
            if question is None:
                continue
            result = self.aggregator.aggregate(question.code, question_responses, experts_by_id)
            if result is not None:
                aggregated[question.code] = result
        return aggregated

    def _rule_confidence(
        self, rule: Rule, aggregated_answers: dict[str, AggregatedAnswer]
    ) -> tuple[float, int, bool]:
        """A rule's confidence is the average confidence of the aggregated answers
        referenced by its conditions. Rules that only reference case subject data
        (no expert-answered questions) default to full confidence."""
        referenced_codes = [
            c.attribute_path.split(":", 1)[1]
            for c in rule.conditions
            if c.attribute_path.startswith("question:")
        ]
        relevant_answers = [
            aggregated_answers[c] for c in referenced_codes if c in aggregated_answers
        ]

        if not relevant_answers:
            return 1.0, 0, False

        avg_confidence = sum(a.confidence for a in relevant_answers) / len(relevant_answers)
        total_experts = sum(a.contributing_expert_count for a in relevant_answers)
        conflict = any(a.conflict_detected for a in relevant_answers)
        return avg_confidence, total_experts, conflict

"""Combines potentially conflicting expert Responses to the same Question into a
single, explainable aggregated answer, weighting each expert's contribution by
their configured trust weight and their stated confidence for that answer."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from numbers import Number
from typing import Any

from app.models.expert import Expert
from app.models.response import Response

# If the top-weighted categorical answer holds less than this fraction of total
# weight, the aggregator flags the result as conflicted.
AGREEMENT_THRESHOLD = 0.6

# For numeric answers, a coefficient of variation above this threshold indicates
# meaningful disagreement among experts.
NUMERIC_CONFLICT_CV_THRESHOLD = 0.25


@dataclass
class ExpertContribution:
    expert_id: str
    expert_weight: float
    response_confidence: float
    effective_weight: float
    value: Any


@dataclass
class AggregatedAnswer:
    question_code: str
    value: Any
    confidence: float
    conflict_detected: bool
    contributing_expert_count: int
    contributions: list[ExpertContribution] = field(default_factory=list)

    def to_trace(self) -> dict[str, Any]:
        return {
            "question_code": self.question_code,
            "value": self.value,
            "confidence": round(self.confidence, 4),
            "conflict_detected": self.conflict_detected,
            "contributing_expert_count": self.contributing_expert_count,
            "contributions": [
                {
                    "expert_id": c.expert_id,
                    "expert_weight": c.expert_weight,
                    "response_confidence": c.response_confidence,
                    "effective_weight": round(c.effective_weight, 4),
                    "value": c.value,
                }
                for c in self.contributions
            ],
        }


def _extract_scalar(answer_value: dict[str, Any]) -> Any:
    """Response.answer_value is stored as JSON; convention is {"value": <scalar>}."""
    return answer_value.get("value") if isinstance(answer_value, dict) else answer_value


class ExpertOpinionAggregator:
    """Aggregates multiple expert Responses for the same question into one answer."""

    def aggregate(
        self,
        question_code: str,
        responses: list[Response],
        experts_by_id: dict[str, Expert],
    ) -> AggregatedAnswer | None:
        if not responses:
            return None

        contributions: list[ExpertContribution] = []
        for response in responses:
            expert = experts_by_id.get(str(response.expert_id))
            expert_weight = float(expert.weight) if expert is not None else 1.0
            response_confidence = float(response.confidence)
            effective_weight = expert_weight * response_confidence
            value = _extract_scalar(response.answer_value)
            contributions.append(
                ExpertContribution(
                    expert_id=str(response.expert_id),
                    expert_weight=expert_weight,
                    response_confidence=response_confidence,
                    effective_weight=effective_weight,
                    value=value,
                )
            )

        total_weight = sum(c.effective_weight for c in contributions) or 1.0
        avg_confidence = (
            sum(c.response_confidence * c.effective_weight for c in contributions) / total_weight
        )

        if all(
            isinstance(c.value, Number) and not isinstance(c.value, bool) for c in contributions
        ):
            aggregated_value, conflict = self._aggregate_numeric(contributions, total_weight)
        else:
            aggregated_value, conflict = self._aggregate_categorical(contributions, total_weight)

        return AggregatedAnswer(
            question_code=question_code,
            value=aggregated_value,
            confidence=avg_confidence,
            conflict_detected=conflict,
            contributing_expert_count=len(contributions),
            contributions=contributions,
        )

    def _aggregate_numeric(
        self, contributions: list[ExpertContribution], total_weight: float
    ) -> tuple[float, bool]:
        weighted_mean = sum(c.value * c.effective_weight for c in contributions) / total_weight
        if len(contributions) < 2:
            return weighted_mean, False
        variance = (
            sum(c.effective_weight * (c.value - weighted_mean) ** 2 for c in contributions)
            / total_weight
        )
        std_dev = variance**0.5
        coefficient_of_variation = std_dev / abs(weighted_mean) if weighted_mean else std_dev
        conflict = coefficient_of_variation > NUMERIC_CONFLICT_CV_THRESHOLD
        return weighted_mean, conflict

    def _aggregate_categorical(
        self, contributions: list[ExpertContribution], total_weight: float
    ) -> tuple[Any, bool]:
        weight_by_value: dict[Any, float] = defaultdict(float)
        for c in contributions:
            weight_by_value[c.value] += c.effective_weight

        winner_value, winner_weight = max(weight_by_value.items(), key=lambda kv: kv[1])
        agreement_ratio = winner_weight / total_weight if total_weight else 0.0
        conflict = agreement_ratio < AGREEMENT_THRESHOLD or (
            len(weight_by_value) > 1 and agreement_ratio < 0.8
        )
        return winner_value, conflict

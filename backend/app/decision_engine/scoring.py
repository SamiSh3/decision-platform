"""Maps an aggregate weighted score in [-1, 1] to a RecommendationLabel."""

from __future__ import annotations

from app.core.constants import RecommendationLabel

# Score thresholds; overall_score is normalized to the range [-1, 1].
_THRESHOLDS: list[tuple[float, RecommendationLabel]] = [
    (0.6, RecommendationLabel.STRONGLY_RECOMMENDED),
    (0.2, RecommendationLabel.RECOMMENDED),
    (-0.2, RecommendationLabel.NEUTRAL),
    (-0.6, RecommendationLabel.NOT_RECOMMENDED),
]


def score_to_label(score: float) -> RecommendationLabel:
    for threshold, label in _THRESHOLDS:
        if score >= threshold:
            return label
    return RecommendationLabel.STRONGLY_NOT_RECOMMENDED

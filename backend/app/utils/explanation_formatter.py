"""Renders a DecisionResult's structured `explanation` JSON as human-readable
plain text, for API consumers (or notifications/emails) that want a summary
rather than the raw explanation trace."""

from __future__ import annotations

from typing import Any

_RECOMMENDATION_LABELS = {
    "strongly_recommended": "Strongly Recommended",
    "recommended": "Recommended",
    "neutral": "Neutral",
    "not_recommended": "Not Recommended",
    "strongly_not_recommended": "Strongly Not Recommended",
}


def format_decision_explanation(
    recommendation: str,
    overall_score: float,
    overall_confidence: float,
    explanation: dict[str, Any],
) -> str:
    label = _RECOMMENDATION_LABELS.get(recommendation, recommendation)
    lines = [
        f"Recommendation: {label}",
        f"Overall score: {overall_score:+.2f} (confidence: {overall_confidence:.0%})",
        "",
    ]

    matched_rules = explanation.get("matched_rules", [])
    if not matched_rules:
        lines.append("No rules matched the available case data.")
    else:
        lines.append(f"{len(matched_rules)} rule(s) contributed to this recommendation:")
        for rule in matched_rules:
            conflict_note = (
                " [conflicting expert opinions]" if rule.get("conflict_detected") else ""
            )
            lines.append(
                f"  - {rule['rule_name']} (impact {rule['score_impact']:+.2f}, "
                f"confidence {rule['confidence']:.0%}){conflict_note}: {rule['explanation']}"
            )

    if explanation.get("conflicts_detected"):
        lines.append("")
        lines.append(
            "Note: experts disagreed on at least one input used by this decision; "
            "see the confidence scores for details."
        )

    return "\n".join(lines)

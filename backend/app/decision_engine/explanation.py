"""Renders human-readable explanations from rule outcome templates."""

from __future__ import annotations

import re
from typing import Any

from app.decision_engine.aggregator import AggregatedAnswer

_PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z0-9_]+)\}")


def render_template(
    template: str,
    subject_data: dict[str, Any],
    aggregated_answers: dict[str, AggregatedAnswer],
) -> str:
    """Fills `{field}` placeholders from subject_data first, then from aggregated
    question answers (by question code). Unknown placeholders are left as-is
    rather than raising, so templates remain robust to missing optional data."""

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key in subject_data:
            return str(subject_data[key])
        if key in aggregated_answers:
            return str(aggregated_answers[key].value)
        return match.group(0)

    return _PLACEHOLDER_RE.sub(_replace, template)

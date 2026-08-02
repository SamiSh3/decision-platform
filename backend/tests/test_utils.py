"""Unit tests for backend/app/utils."""

from __future__ import annotations

from app.utils.explanation_formatter import format_decision_explanation
from app.utils.pagination import clamp_page, compute_total_pages


def test_compute_total_pages_basic() -> None:
    assert compute_total_pages(total=95, page_size=20) == 5
    assert compute_total_pages(total=100, page_size=20) == 5
    assert compute_total_pages(total=101, page_size=20) == 6
    assert compute_total_pages(total=0, page_size=20) == 0


def test_compute_total_pages_zero_page_size_is_safe() -> None:
    assert compute_total_pages(total=10, page_size=0) == 0


def test_clamp_page_within_range() -> None:
    assert clamp_page(page=3, total_pages=5) == 3
    assert clamp_page(page=99, total_pages=5) == 5
    assert clamp_page(page=0, total_pages=5) == 1
    assert clamp_page(page=1, total_pages=0) == 1


def test_format_decision_explanation_with_matched_rules() -> None:
    text = format_decision_explanation(
        recommendation="recommended",
        overall_score=0.4,
        overall_confidence=0.9,
        explanation={
            "matched_rules": [
                {
                    "rule_name": "Fair price",
                    "score_impact": 0.3,
                    "confidence": 1.0,
                    "conflict_detected": False,
                    "explanation": "Asking price is fair.",
                }
            ],
            "conflicts_detected": False,
        },
    )
    assert "Recommended" in text
    assert "Fair price" in text
    assert "Asking price is fair." in text
    assert "conflicting expert opinions" not in text


def test_format_decision_explanation_flags_conflicts() -> None:
    text = format_decision_explanation(
        recommendation="neutral",
        overall_score=0.0,
        overall_confidence=0.5,
        explanation={
            "matched_rules": [
                {
                    "rule_name": "Engine condition",
                    "score_impact": 0.2,
                    "confidence": 0.5,
                    "conflict_detected": True,
                    "explanation": "Experts disagreed on engine condition.",
                }
            ],
            "conflicts_detected": True,
        },
    )
    assert "conflicting expert opinions" in text
    assert "experts disagreed" in text.lower()


def test_format_decision_explanation_no_matched_rules() -> None:
    text = format_decision_explanation(
        recommendation="not_recommended",
        overall_score=0.0,
        overall_confidence=0.0,
        explanation={"matched_rules": [], "conflicts_detected": False},
    )
    assert "No rules matched" in text

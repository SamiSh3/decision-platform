"""Tests for the KnowledgeCaptureValidator quality heuristics."""

from __future__ import annotations

from app.core.constants import RiskLevel
from app.knowledge.capture_validator import KnowledgeCaptureValidator


def test_high_risk_without_reasoning_is_invalid() -> None:
    validator = KnowledgeCaptureValidator()
    result = validator.validate(
        confidence=0.9,
        risk=RiskLevel.HIGH,
        reasoning=None,
        exceptions=None,
        conditions=None,
        evidence_count=0,
    )
    assert result.is_valid is False
    assert any(issue.field_name == "reasoning" for issue in result.issues)
    assert any(issue.field_name == "evidence" for issue in result.issues)


def test_high_risk_with_reasoning_and_evidence_is_valid() -> None:
    validator = KnowledgeCaptureValidator()
    result = validator.validate(
        confidence=0.9,
        risk=RiskLevel.HIGH,
        reasoning=(
            "Detailed inspection revealed structural damage consistent with a prior collision."
        ),
        exceptions=None,
        conditions="Applies when vehicle history report confirms accident record.",
        evidence_count=1,
    )
    assert result.is_valid is True
    assert result.issues == []


def test_low_confidence_requires_reasoning() -> None:
    validator = KnowledgeCaptureValidator()
    result = validator.validate(
        confidence=0.2,
        risk=RiskLevel.LOW,
        reasoning=None,
        exceptions=None,
        conditions=None,
        evidence_count=0,
    )
    assert result.is_valid is False


def test_exceptions_without_conditions_is_invalid() -> None:
    validator = KnowledgeCaptureValidator()
    result = validator.validate(
        confidence=0.9,
        risk=RiskLevel.LOW,
        reasoning="Solid reasoning provided here for the answer given.",
        exceptions="Unless the vehicle was recently repainted.",
        conditions=None,
        evidence_count=0,
    )
    assert result.is_valid is False
    assert any(issue.field_name == "conditions" for issue in result.issues)

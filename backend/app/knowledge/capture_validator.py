"""Validation rules for expert knowledge capture.

Ensures every expert answer meets the platform's quality bar before it is trusted
by the decision engine: sufficiently justified when confidence or risk is high,
and internally consistent (e.g. exceptions require conditions to be stated too).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.constants import RiskLevel


@dataclass
class ValidationIssue:
    field_name: str
    message: str


@dataclass
class ValidationResult:
    is_valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)


class KnowledgeCaptureValidator:
    """Applies knowledge-quality heuristics to a candidate expert response payload."""

    MIN_REASONING_LENGTH_FOR_HIGH_RISK = 20

    def validate(
        self,
        *,
        confidence: float,
        risk: RiskLevel,
        reasoning: str | None,
        exceptions: str | None,
        conditions: str | None,
        evidence_count: int,
    ) -> ValidationResult:
        issues: list[ValidationIssue] = []

        if risk in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            if not reasoning or len(reasoning.strip()) < self.MIN_REASONING_LENGTH_FOR_HIGH_RISK:
                issues.append(
                    ValidationIssue(
                        "reasoning",
                        "High or critical risk answers require detailed reasoning "
                        f"(at least {self.MIN_REASONING_LENGTH_FOR_HIGH_RISK} characters).",
                    )
                )
            if evidence_count == 0:
                issues.append(
                    ValidationIssue(
                        "evidence", "High or critical risk answers should be backed by evidence."
                    )
                )

        if confidence < 0.4 and not reasoning:
            issues.append(
                ValidationIssue(
                    "reasoning", "Low-confidence answers must explain why confidence is low."
                )
            )

        if exceptions and not conditions:
            issues.append(
                ValidationIssue(
                    "conditions",
                    "Exceptions were provided without the conditions under which the "
                    "answer normally holds; please describe the base conditions too.",
                )
            )

        return ValidationResult(is_valid=len(issues) == 0, issues=issues)

"""Rule-based decision engine.

Given a Case, matches applicable Rules against aggregated expert responses and
case subject data, resolves conflicting expert opinions through expert-weighted
confidence scoring, and produces an explainable DecisionResult.
"""

ENGINE_VERSION = "1.0.0"

"""Tests for rule creation and immutable versioning via the API."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_create_rule_with_conditions_and_outcomes(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    domain = client.post(
        "/api/v1/domains",
        json={"code": "procurement", "name": "Procurement"},
        headers=admin_headers,
    ).json()

    rule = client.post(
        "/api/v1/rules",
        json={
            "domain_id": domain["id"],
            "code": "vendor_risk",
            "name": "Vendor risk",
            "status": "active",
            "conditions": [
                {
                    "attribute_path": "subject:vendor_score",
                    "operator": "less_than",
                    "value": 50,
                }
            ],
            "outcomes": [
                {
                    "direction": "caution",
                    "score_impact": -0.5,
                    "explanation_template": "Vendor score {vendor_score} is below threshold.",
                }
            ],
        },
        headers=admin_headers,
    )
    assert rule.status_code == 201
    body = rule.json()
    assert body["version"] == 1
    assert len(body["conditions"]) == 1
    assert len(body["outcomes"]) == 1


def test_new_rule_version_is_independent_draft(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    domain = client.post(
        "/api/v1/domains", json={"code": "investment", "name": "Investment"}, headers=admin_headers
    ).json()

    original = client.post(
        "/api/v1/rules",
        json={
            "domain_id": domain["id"],
            "code": "risk_tolerance",
            "name": "Risk tolerance",
            "status": "active",
            "conditions": [
                {"attribute_path": "subject:volatility", "operator": "greater_than", "value": 0.3}
            ],
            "outcomes": [
                {
                    "direction": "caution",
                    "score_impact": -0.4,
                    "explanation_template": "Volatility {volatility} exceeds tolerance.",
                }
            ],
        },
        headers=admin_headers,
    ).json()

    new_version = client.post(f"/api/v1/rules/{original['id']}/new-version", headers=admin_headers)
    assert new_version.status_code == 201
    body = new_version.json()
    assert body["version"] == 2
    assert body["status"] == "draft"
    assert body["code"] == original["code"]
    assert len(body["conditions"]) == len(original["conditions"])

    # The original rule remains unchanged and active.
    original_reloaded = client.get(f"/api/v1/rules/{original['id']}", headers=admin_headers).json()
    assert original_reloaded["version"] == 1
    assert original_reloaded["status"] == "active"

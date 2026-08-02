"""Tests for Questionnaire immutable versioning (mirrors Rule versioning)."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient


def _create_domain(client: TestClient, admin_headers: dict[str, str], code: str) -> dict:
    response = client.post(
        "/api/v1/domains", json={"code": code, "name": code.title()}, headers=admin_headers
    )
    assert response.status_code == 201
    return response.json()


def test_new_questionnaire_version_copies_questions_without_mutating_original(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    domain = _create_domain(client, admin_headers, "real_estate")

    original = client.post(
        "/api/v1/questionnaires",
        json={
            "domain_id": domain["id"],
            "code": "property_inspection",
            "title": "Property Inspection",
        },
        headers=admin_headers,
    ).json()

    client.post(
        f"/api/v1/questionnaires/{original['id']}/questions",
        json={
            "code": "roof_condition",
            "text": "What is the roof condition?",
            "question_type": "single_choice",
            "options": [
                {"value": "good", "label": "Good", "display_order": 1},
                {"value": "poor", "label": "Poor", "display_order": 2},
            ],
        },
        headers=admin_headers,
    )

    new_version = client.post(
        f"/api/v1/questionnaires/{original['id']}/new-version", headers=admin_headers
    )
    assert new_version.status_code == 201
    body = new_version.json()
    assert body["version"] == 2
    assert body["is_active"] is False
    assert body["code"] == original["code"]
    assert len(body["questions"]) == 1
    assert len(body["questions"][0]["options"]) == 2

    original_reloaded = client.get(
        f"/api/v1/questionnaires/{original['id']}", headers=admin_headers
    ).json()
    assert original_reloaded["version"] == 1
    assert original_reloaded["is_active"] is True
    assert len(original_reloaded["questions"]) == 1


def test_new_questionnaire_version_requires_admin(
    client: TestClient, admin_headers: dict[str, str], user_headers: dict[str, str]
) -> None:
    domain = _create_domain(client, admin_headers, "insurance")
    questionnaire = client.post(
        "/api/v1/questionnaires",
        json={"domain_id": domain["id"], "code": "policy_review", "title": "Policy Review"},
        headers=admin_headers,
    ).json()

    response = client.post(
        f"/api/v1/questionnaires/{questionnaire['id']}/new-version", headers=user_headers
    )
    assert response.status_code == 403


def test_new_version_of_unknown_questionnaire_returns_404(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    response = client.post(
        f"/api/v1/questionnaires/{uuid.uuid4()}/new-version", headers=admin_headers
    )
    assert response.status_code == 404

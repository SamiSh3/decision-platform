"""Tests covering domains, questionnaires/questions, cases and expert responses."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _create_domain(client: TestClient, admin_headers: dict[str, str]) -> dict:
    response = client.post(
        "/api/v1/domains",
        json={"code": "used_car_purchase", "name": "Used Car Purchase Decision"},
        headers=admin_headers,
    )
    assert response.status_code == 201
    return response.json()


def _create_questionnaire_with_question(
    client: TestClient, admin_headers: dict[str, str], domain_id: str
) -> dict:
    questionnaire = client.post(
        "/api/v1/questionnaires",
        json={"domain_id": domain_id, "code": "inspection", "title": "Inspection"},
        headers=admin_headers,
    ).json()
    question = client.post(
        f"/api/v1/questionnaires/{questionnaire['id']}/questions",
        json={
            "code": "mileage",
            "text": "What is the mileage?",
            "question_type": "numeric",
        },
        headers=admin_headers,
    ).json()
    return {"questionnaire": questionnaire, "question": question}


def test_case_lifecycle(
    client: TestClient, admin_headers: dict[str, str], user_headers: dict[str, str]
) -> None:
    domain = _create_domain(client, admin_headers)

    create_response = client.post(
        "/api/v1/cases",
        json={
            "domain_id": domain["id"],
            "title": "Sample case",
            "subject_data": {"make": "Toyota"},
        },
        headers=user_headers,
    )
    assert create_response.status_code == 201
    case = create_response.json()
    assert case["status"] == "draft"

    get_response = client.get(f"/api/v1/cases/{case['id']}", headers=user_headers)
    assert get_response.status_code == 200

    update_response = client.patch(
        f"/api/v1/cases/{case['id']}", json={"status": "in_progress"}, headers=user_headers
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "in_progress"

    list_response = client.get("/api/v1/cases", headers=user_headers)
    assert list_response.status_code == 200
    assert list_response.json()["total"] >= 1

    delete_response = client.delete(f"/api/v1/cases/{case['id']}", headers=user_headers)
    assert delete_response.status_code == 200


def test_expert_can_submit_response_with_full_knowledge_fields(
    client: TestClient,
    admin_headers: dict[str, str],
    expert_headers: dict[str, str],
    user_headers: dict[str, str],
    expert_user,
) -> None:
    domain = _create_domain(client, admin_headers)
    setup = _create_questionnaire_with_question(client, admin_headers, domain["id"])

    case = client.post(
        "/api/v1/cases",
        json={"domain_id": domain["id"], "title": "Case for response test"},
        headers=user_headers,
    ).json()

    expert_profile = client.post(
        "/api/v1/experts",
        json={
            "user_id": str(expert_user.id),
            "specialty": "Mechanics",
            "years_experience": 10,
            "weight": 1.4,
        },
        headers=admin_headers,
    )
    assert expert_profile.status_code == 201
    expert_id = expert_profile.json()["id"]

    response_payload = {
        "case_id": case["id"],
        "question_id": setup["question"]["id"],
        "expert_id": expert_id,
        "answer_value": {"value": 45000},
        "confidence": 0.9,
        "reasoning": "Odometer reading verified against maintenance records.",
        "conditions": "Assuming odometer has not been tampered with.",
        "importance": "high",
        "risk": "medium",
        "notes": "Checked twice.",
        "references": ["Vehicle history report"],
    }
    create = client.post("/api/v1/responses", json=response_payload, headers=expert_headers)
    assert create.status_code == 201
    body = create.json()
    assert body["confidence"] == 0.9
    assert body["reasoning"] == response_payload["reasoning"]

    listed = client.get(f"/api/v1/cases/{case['id']}/responses", headers=expert_headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_evaluate_case_and_read_plain_text_explanation(
    client: TestClient,
    admin_headers: dict[str, str],
    expert_headers: dict[str, str],
    user_headers: dict[str, str],
    expert_user,
) -> None:
    domain = _create_domain(client, admin_headers)
    setup = _create_questionnaire_with_question(client, admin_headers, domain["id"])

    case = client.post(
        "/api/v1/cases",
        json={"domain_id": domain["id"], "title": "Case for explanation test"},
        headers=user_headers,
    ).json()

    expert_profile = client.post(
        "/api/v1/experts",
        json={"user_id": str(expert_user.id), "specialty": "Mechanics", "years_experience": 8},
        headers=admin_headers,
    ).json()

    client.post(
        "/api/v1/responses",
        json={
            "case_id": case["id"],
            "question_id": setup["question"]["id"],
            "expert_id": expert_profile["id"],
            "answer_value": {"value": 30000},
            "confidence": 0.9,
        },
        headers=expert_headers,
    )

    rule = client.post(
        "/api/v1/rules",
        json={
            "domain_id": domain["id"],
            "code": "low_mileage_bonus",
            "name": "Low mileage bonus",
            "status": "active",
            "conditions": [
                {"attribute_path": "question:mileage", "operator": "less_than", "value": 50000}
            ],
            "outcomes": [
                {
                    "direction": "buy",
                    "score_impact": 0.4,
                    "explanation_template": "Low mileage bonus rule matched.",
                }
            ],
        },
        headers=admin_headers,
    )
    assert rule.status_code == 201

    evaluation = client.post(f"/api/v1/cases/{case['id']}/evaluate", headers=user_headers)
    assert evaluation.status_code == 201
    result_id = evaluation.json()["id"]

    explanation = client.get(
        f"/api/v1/decision-results/{result_id}/explanation", headers=user_headers
    )
    assert explanation.status_code == 200
    assert "Recommended" in explanation.text or "Neutral" in explanation.text
    assert "Low mileage bonus rule matched." in explanation.text

"""Tests for Role Based Access Control enforcement."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_non_admin_cannot_create_domain(client: TestClient, user_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/v1/domains",
        json={"code": "real_estate", "name": "Real Estate"},
        headers=user_headers,
    )
    assert response.status_code == 403


def test_admin_can_create_domain(client: TestClient, admin_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/v1/domains",
        json={"code": "real_estate", "name": "Real Estate"},
        headers=admin_headers,
    )
    assert response.status_code == 201
    assert response.json()["code"] == "real_estate"


def test_any_authenticated_user_can_list_domains(
    client: TestClient, admin_headers: dict[str, str], user_headers: dict[str, str]
) -> None:
    client.post(
        "/api/v1/domains", json={"code": "insurance", "name": "Insurance"}, headers=admin_headers
    )
    response = client.get("/api/v1/domains", headers=user_headers)
    assert response.status_code == 200


def test_unauthenticated_request_rejected(client: TestClient) -> None:
    response = client.get("/api/v1/domains")
    assert response.status_code == 401


def test_expert_cannot_manage_users(client: TestClient, expert_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/v1/users",
        json={
            "email": "should-not-be-created@test.example",
            "password": "StrongPass123!",
            "full_name": "Nope",
            "role": "user",
        },
        headers=expert_headers,
    )
    assert response.status_code == 403


def test_reviewer_can_read_audit_logs_but_user_cannot(
    client: TestClient, reviewer_headers: dict[str, str], user_headers: dict[str, str]
) -> None:
    reviewer_response = client.get("/api/v1/audit-logs", headers=reviewer_headers)
    assert reviewer_response.status_code == 200

    user_response = client.get("/api/v1/audit-logs", headers=user_headers)
    assert user_response.status_code == 403

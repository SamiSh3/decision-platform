"""Tests for the /health endpoint's database connectivity check."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_check_reports_ok_when_database_is_reachable(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert "app" in body
    assert "env" in body


def test_health_check_requires_no_authentication(client: TestClient) -> None:
    # No Authorization header at all - /health must remain public for load balancers.
    response = client.get("/health")
    assert response.status_code != 401

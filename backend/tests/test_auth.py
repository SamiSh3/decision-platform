"""Tests for authentication: register, login, refresh, current user."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.models.user import Role, User


def test_register_creates_user_with_default_role(
    client: TestClient, roles: dict[str, Role]
) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new-user@test.example",
            "password": "StrongPass123!",
            "full_name": "New User",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new-user@test.example"
    assert body["is_active"] is True


def test_register_duplicate_email_conflicts(client: TestClient, roles: dict[str, Role]) -> None:
    payload = {
        "email": "dupe@test.example",
        "password": "StrongPass123!",
        "full_name": "Dupe User",
    }
    first = client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201
    second = client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409


def test_login_success_returns_tokens(client: TestClient, plain_user: User) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": plain_user.email, "password": "Password123!"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password_rejected(client: TestClient, plain_user: User) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": plain_user.email, "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_login_unknown_email_rejected(client: TestClient, roles: dict[str, Role]) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@test.example", "password": "whatever123"},
    )
    assert response.status_code == 401


def test_refresh_token_issues_new_access_token(client: TestClient, plain_user: User) -> None:
    login = client.post(
        "/api/v1/auth/login", json={"email": plain_user.email, "password": "Password123!"}
    )
    refresh_token = login.json()["refresh_token"]
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_get_current_user_requires_token(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_get_current_user_with_valid_token(
    client: TestClient, user_headers: dict[str, str]
) -> None:
    response = client.get("/api/v1/auth/me", headers=user_headers)
    assert response.status_code == 200
    assert "email" in response.json()

"""Tests for the Permission catalog, Role<->Permission grants, and the
`require_permissions` fine-grained authorization dependency."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.permission import Permission, RolePermission
from app.models.user import Role


def test_admin_can_create_and_list_permissions(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    response = client.post(
        "/api/v1/permissions",
        json={"code": "cases:publish", "resource": "cases", "action": "publish"},
        headers=admin_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["code"] == "cases:publish"

    listed = client.get("/api/v1/permissions", headers=admin_headers)
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1


def test_duplicate_permission_code_conflicts(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    payload = {"code": "rules:publish", "resource": "rules", "action": "publish"}
    first = client.post("/api/v1/permissions", json=payload, headers=admin_headers)
    assert first.status_code == 201
    second = client.post("/api/v1/permissions", json=payload, headers=admin_headers)
    assert second.status_code == 409


def test_non_admin_cannot_create_permission(
    client: TestClient, user_headers: dict[str, str]
) -> None:
    response = client.post(
        "/api/v1/permissions",
        json={"code": "cases:archive", "resource": "cases", "action": "archive"},
        headers=user_headers,
    )
    assert response.status_code == 403


def test_grant_and_revoke_permission_to_role(
    client: TestClient, admin_headers: dict[str, str], roles: dict[str, Role]
) -> None:
    permission = client.post(
        "/api/v1/permissions",
        json={"code": "domains:archive", "resource": "domains", "action": "archive"},
        headers=admin_headers,
    ).json()

    grant = client.post(
        "/api/v1/permissions/grants",
        json={"role_id": str(roles["reviewer"].id), "permission_id": permission["id"]},
        headers=admin_headers,
    )
    assert grant.status_code == 201
    grant_id = grant.json()["id"]

    duplicate_grant = client.post(
        "/api/v1/permissions/grants",
        json={"role_id": str(roles["reviewer"].id), "permission_id": permission["id"]},
        headers=admin_headers,
    )
    assert duplicate_grant.status_code == 409

    listed = client.get(
        f"/api/v1/permissions/roles/{roles['reviewer'].id}/grants", headers=admin_headers
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    revoke = client.delete(f"/api/v1/permissions/grants/{grant_id}", headers=admin_headers)
    assert revoke.status_code == 200

    listed_after = client.get(
        f"/api/v1/permissions/roles/{roles['reviewer'].id}/grants", headers=admin_headers
    )
    assert len(listed_after.json()) == 0


def test_role_permission_codes_reflect_active_grants(
    db_session: Session, roles: dict[str, Role]
) -> None:
    permission = Permission(code="knowledge:curate", resource="knowledge", action="curate")
    db_session.add(permission)
    db_session.flush()

    grant = RolePermission(role_id=roles["expert"].id, permission_id=permission.id)
    db_session.add(grant)
    db_session.commit()
    db_session.refresh(roles["expert"])

    assert "knowledge:curate" in roles["expert"].permission_codes

    grant.is_deleted = True
    db_session.add(grant)
    db_session.commit()
    db_session.refresh(roles["expert"])

    assert "knowledge:curate" not in roles["expert"].permission_codes

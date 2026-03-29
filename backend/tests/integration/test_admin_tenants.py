"""Admin auth and tenant CRUD against a real Postgres (see tests/integration/conftest.py)."""

from __future__ import annotations

import uuid
from typing import Any

import pytest

pytestmark = pytest.mark.integration

AdminCreds = dict[str, Any]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_login_and_me(integration_client, integration_admin_credentials: AdminCreds) -> None:
    r = integration_client.post(
        "/api/auth/login",
        json={
            "email": integration_admin_credentials["email"],
            "password": integration_admin_credentials["password"],
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["expires_in"] > 0

    me = integration_client.get(
        "/api/auth/me",
        headers=_auth_headers(body["access_token"]),
    )
    assert me.status_code == 200
    assert me.json()["email"] == integration_admin_credentials["email"]
    assert me.json()["role"] == "super_admin"


def test_login_rejects_bad_password(
    integration_client,
    integration_admin_credentials: AdminCreds,
) -> None:
    r = integration_client.post(
        "/api/auth/login",
        json={"email": integration_admin_credentials["email"], "password": "wrong-password"},
    )
    assert r.status_code == 401


def test_me_requires_auth(integration_client) -> None:
    r = integration_client.get("/api/auth/me")
    assert r.status_code == 401


def test_tenant_crud_super_admin(
    integration_client,
    integration_admin_credentials: AdminCreds,
) -> None:
    login = integration_client.post(
        "/api/auth/login",
        json={
            "email": integration_admin_credentials["email"],
            "password": integration_admin_credentials["password"],
        },
    )
    token = login.json()["access_token"]
    headers = _auth_headers(token)

    slug = f"it-{uuid.uuid4().hex[:10]}"
    create_body = {
        "name": "Integration Tenant",
        "slug": slug,
        "base_url": "https://example.edu",
        "allowed_domains": ["example.edu"],
        "branding": {"app_title": "IT"},
    }
    c = integration_client.post("/api/admin/tenants", json=create_body, headers=headers)
    assert c.status_code == 201, c.text
    tid = c.json()["id"]
    assert c.json()["slug"] == slug

    listed = integration_client.get("/api/admin/tenants", headers=headers)
    assert listed.status_code == 200
    assert any(t["id"] == tid for t in listed.json())

    one = integration_client.get(f"/api/admin/tenants/{tid}", headers=headers)
    assert one.status_code == 200
    assert one.json()["name"] == "Integration Tenant"

    patched = integration_client.patch(
        f"/api/admin/tenants/{tid}",
        json={"name": "Integration Tenant Updated"},
        headers=headers,
    )
    assert patched.status_code == 200
    assert patched.json()["name"] == "Integration Tenant Updated"

    dup = integration_client.post("/api/admin/tenants", json=create_body, headers=headers)
    assert dup.status_code == 409

    deleted = integration_client.delete(f"/api/admin/tenants/{tid}", headers=headers)
    assert deleted.status_code == 204

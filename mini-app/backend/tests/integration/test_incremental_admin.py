"""Incremental admin routes (auth + job creation wiring)."""

from __future__ import annotations

import uuid

import pytest

pytestmark = pytest.mark.integration


def test_incremental_endpoints_require_auth(integration_client) -> None:
    r = integration_client.post(
        "/api/admin/tenants/1/incremental/refresh-page",
        json={"crawl_config_id": 1, "url": "https://example.edu/a"},
    )
    assert r.status_code == 401


def test_incremental_refresh_page_creates_queued_job(
    integration_client,
    integration_admin_credentials: dict,
    integration_database_url: str,
) -> None:
    login = integration_client.post(
        "/api/auth/login",
        json={
            "email": integration_admin_credentials["email"],
            "password": integration_admin_credentials["password"],
        },
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    slug = f"inc-{uuid.uuid4().hex[:10]}"
    t = integration_client.post(
        "/api/admin/tenants",
        json={
            "name": "Inc Tenant",
            "slug": slug,
            "base_url": "https://example.edu",
            "allowed_domains": ["example.edu"],
        },
        headers=headers,
    )
    assert t.status_code == 201, t.text
    tenant_id = t.json()["id"]

    cfg = integration_client.post(
        f"/api/admin/tenants/{tenant_id}/crawl-configs",
        json={
            "name": "Main",
            "base_url": "https://example.edu/",
            "allowed_hosts": ["example.edu"],
        },
        headers=headers,
    )
    assert cfg.status_code == 201, cfg.text
    crawl_config_id = cfg.json()["id"]

    r = integration_client.post(
        f"/api/admin/tenants/{tenant_id}/incremental/refresh-page",
        json={"crawl_config_id": crawl_config_id, "url": "https://example.edu/page"},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "queued"
    assert body["job_type"] == "incremental_url"
    assert body["workflow"] == "refresh_page"
    assert body["stats"]["seed_url"] == "https://example.edu/page"


def test_incremental_refresh_pdf_creates_queued_job(
    integration_client,
    integration_admin_credentials: dict,
) -> None:
    login = integration_client.post(
        "/api/auth/login",
        json={
            "email": integration_admin_credentials["email"],
            "password": integration_admin_credentials["password"],
        },
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    slug = f"pdf-{uuid.uuid4().hex[:10]}"
    t = integration_client.post(
        "/api/admin/tenants",
        json={
            "name": "Pdf Tenant",
            "slug": slug,
            "base_url": "https://example.edu",
            "allowed_domains": ["example.edu"],
        },
        headers=headers,
    )
    assert t.status_code == 201, t.text
    tenant_id = t.json()["id"]

    cfg = integration_client.post(
        f"/api/admin/tenants/{tenant_id}/crawl-configs",
        json={
            "name": "Main",
            "base_url": "https://example.edu/",
            "allowed_hosts": ["example.edu"],
        },
        headers=headers,
    )
    assert cfg.status_code == 201, cfg.text
    crawl_config_id = cfg.json()["id"]

    r = integration_client.post(
        f"/api/admin/tenants/{tenant_id}/incremental/refresh-pdf",
        json={"crawl_config_id": crawl_config_id, "url": "https://example.edu/doc.pdf"},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "queued"
    assert body["job_type"] == "incremental_pdf"
    assert body["workflow"] == "refresh_pdf"
    assert body["stats"]["seed_url"] == "https://example.edu/doc.pdf"

"""Retrieval debug API (requires Postgres + indexed chunks for full behavior)."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


def test_retrieval_debug_requires_auth(integration_client) -> None:
    r = integration_client.post(
        "/api/admin/tenants/1/retrieval/debug",
        json={"query": "tuition"},
    )
    assert r.status_code == 401

"""Chat API auth (integration)."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


def test_chat_query_requires_auth(integration_client) -> None:
    r = integration_client.post(
        "/api/tenants/1/chat/query",
        json={"message": "Hello"},
    )
    assert r.status_code == 401

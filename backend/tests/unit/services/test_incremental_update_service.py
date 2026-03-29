"""Incremental queue helpers build the expected crawl job payloads."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.models.enums import CrawlJobType
from app.services import incremental_update_service


def test_refresh_page_queues_incremental_url(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    def fake_create(session, tenant_id, body, actor, request):
        captured["tenant_id"] = tenant_id
        captured["body"] = body
        return MagicMock()

    monkeypatch.setattr(
        "app.services.incremental_update_service.crawl_job_service.create_job",
        fake_create,
    )

    session = MagicMock()
    actor = MagicMock()
    request = MagicMock()

    incremental_update_service.refresh_page_by_url(
        session,
        tenant_id=3,
        crawl_config_id=7,
        url="https://ex.edu/page",
        actor=actor,
        request=request,
    )

    assert captured["tenant_id"] == 3
    assert captured["body"].job_type == CrawlJobType.incremental_url
    assert str(captured["body"].seed_url) == "https://ex.edu/page"
    assert captured["body"].workflow == "refresh_page"


def test_refresh_pdf_queues_incremental_pdf(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    def fake_create(session, tenant_id, body, actor, request):
        captured["body"] = body
        return MagicMock()

    monkeypatch.setattr(
        "app.services.incremental_update_service.crawl_job_service.create_job",
        fake_create,
    )

    incremental_update_service.refresh_pdf_by_url(
        MagicMock(),
        tenant_id=1,
        crawl_config_id=2,
        url="https://ex.edu/a.pdf",
        actor=MagicMock(),
        request=MagicMock(),
    )

    assert captured["body"].job_type == CrawlJobType.incremental_pdf
    assert str(captured["body"].seed_url) == "https://ex.edu/a.pdf"
    assert captured["body"].workflow == "refresh_pdf"

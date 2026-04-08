"""Crawl job create validation for incremental workflows."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models.enums import CrawlJobType
from app.schemas.crawl_job import CrawlJobCreate


def test_incremental_url_requires_seed() -> None:
    with pytest.raises(ValidationError):
        CrawlJobCreate(crawl_config_id=1, job_type=CrawlJobType.incremental_url)


def test_incremental_pdf_requires_seed() -> None:
    with pytest.raises(ValidationError):
        CrawlJobCreate(crawl_config_id=1, job_type=CrawlJobType.incremental_pdf)


def test_add_source_requires_seed() -> None:
    with pytest.raises(ValidationError):
        CrawlJobCreate(crawl_config_id=1, job_type=CrawlJobType.add_source)


def test_sync_changed_no_seed_ok() -> None:
    j = CrawlJobCreate(crawl_config_id=1, job_type=CrawlJobType.sync_changed)
    assert j.seed_url is None


def test_full_recrawl_no_seed_ok() -> None:
    j = CrawlJobCreate(crawl_config_id=1, job_type=CrawlJobType.full_recrawl)
    assert j.seed_url is None


def test_seed_url_coerced() -> None:
    j = CrawlJobCreate(
        crawl_config_id=1,
        job_type=CrawlJobType.incremental_url,
        seed_url="https://example.edu/page",
        workflow="refresh_page",
    )
    assert str(j.seed_url).startswith("https://example.edu/")

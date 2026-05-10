"""Database-backed `CrawlSink` (create/update `Source` rows)."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.crawler.types import CrawlStats, crawl_stats_to_dict
from app.models.enums import SourceStatus, SourceType
from app.models.job import CrawlJob
from app.models.source import Source
from app.repositories.source import SourceRepository


class DatabaseCrawlSink:
    """Registers crawl output; does not run extraction or indexing."""

    def __init__(
        self,
        session: Session,
        tenant_id: int,
        crawl_config_id: int | None,
        *,
        commit_after_each_source: bool = False,
        job_id: int | None = None,
        prior_job_stats: dict[str, object] | None = None,
        live_stats: CrawlStats | None = None,
    ) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._crawl_config_id = crawl_config_id
        self._repo = SourceRepository(session)
        self._commit_after_each_source = commit_after_each_source
        self._job_id = job_id
        self._prior_job_stats = dict(prior_job_stats or {})
        self._live_stats = live_stats

    def _checkpoint_after_successful_fetch_write(self) -> None:
        """
        Commit each fetched HTML page / PDF registration so work survives crashes.

        Optionally merges running counters into `CrawlJob.stats` before commit.
        """
        if not self._commit_after_each_source:
            return
        if self._job_id is not None and self._live_stats is not None:
            job_row = self._session.get(CrawlJob, self._job_id)
            if job_row is not None:
                merged = {**self._prior_job_stats, **crawl_stats_to_dict(self._live_stats)}
                job_row.stats = merged
        self._session.commit()


    def upsert_html_page(
        self,
        *,
        canonical_url: str,
        fetched_url: str,
        title: str | None,
        parent_source_id: int | None,
    ) -> int:
        now = datetime.now(timezone.utc)
        row = self._repo.get_by_canonical(self._tenant_id, canonical_url)
        if row is None:
            row = Source(
                tenant_id=self._tenant_id,
                crawl_config_id=self._crawl_config_id,
                discovered_from_source_id=parent_source_id,
                url=fetched_url,
                canonical_url=canonical_url,
                title=title,
                source_type=SourceType.html_page,
                status=SourceStatus.discovered,
                last_crawled_at=now,
            )
            self._repo.add(row)
            return row.id
        row.url = fetched_url
        row.last_crawled_at = now
        if title:
            row.title = title
        if row.discovered_from_source_id is None and parent_source_id is not None:
            row.discovered_from_source_id = parent_source_id
        self._session.flush()
        self._checkpoint_after_successful_fetch_write()
        return row.id

    def register_pdf(
        self,
        *,
        canonical_url: str,
        fetched_url: str,
        parent_source_id: int | None,
    ) -> int:
        now = datetime.now(timezone.utc)
        row = self._repo.get_by_canonical(self._tenant_id, canonical_url)
        if row is None:
            row = Source(
                tenant_id=self._tenant_id,
                crawl_config_id=self._crawl_config_id,
                discovered_from_source_id=parent_source_id,
                url=fetched_url,
                canonical_url=canonical_url,
                title=None,
                source_type=SourceType.pdf,
                status=SourceStatus.discovered,
                last_crawled_at=now,
            )
            self._repo.add(row)
            return row.id
        row.url = fetched_url
        row.last_crawled_at = now
        if row.discovered_from_source_id is None and parent_source_id is not None:
            row.discovered_from_source_id = parent_source_id
        self._session.flush()
        self._checkpoint_after_successful_fetch_write()
        return row.id

    def register_html_discovered(
        self,
        *,
        canonical_url: str,
        parent_source_id: int | None,
    ) -> int:
        row = self._repo.get_by_canonical(self._tenant_id, canonical_url)
        if row is None:
            row = Source(
                tenant_id=self._tenant_id,
                crawl_config_id=self._crawl_config_id,
                discovered_from_source_id=parent_source_id,
                url=canonical_url,
                canonical_url=canonical_url,
                title=None,
                source_type=SourceType.html_page,
                status=SourceStatus.discovered,
                last_crawled_at=None,
            )
            self._repo.add(row)
            return row.id
        if row.discovered_from_source_id is None and parent_source_id is not None:
            row.discovered_from_source_id = parent_source_id
        self._session.flush()
        return row.id

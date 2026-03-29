"""Database-backed `CrawlSink` (create/update `Source` rows)."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.enums import SourceStatus, SourceType
from app.models.source import Source
from app.repositories.source import SourceRepository


class DatabaseCrawlSink:
    """Registers crawl output; does not run extraction or indexing."""

    def __init__(
        self,
        session: Session,
        tenant_id: int,
        crawl_config_id: int | None,
    ) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._crawl_config_id = crawl_config_id
        self._repo = SourceRepository(session)

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

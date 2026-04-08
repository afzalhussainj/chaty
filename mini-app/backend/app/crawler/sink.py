"""Callbacks for persisting crawl results (DB or dry-run)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class CrawlSink(Protocol):
    """Persists `Source` rows; HTML fetch vs discovered-only vs PDF registration."""

    def upsert_html_page(
        self,
        *,
        canonical_url: str,
        fetched_url: str,
        title: str | None,
        parent_source_id: int | None,
    ) -> int:
        """Upsert an HTML page that was fetched; returns `sources.id` for lineage."""

    def register_pdf(
        self,
        *,
        canonical_url: str,
        fetched_url: str,
        parent_source_id: int | None,
    ) -> int:
        """Register a PDF discovered or fetched; returns `sources.id`."""

    def register_html_discovered(
        self,
        *,
        canonical_url: str,
        parent_source_id: int | None,
    ) -> int:
        """Single-page mode: record an outgoing HTML link without fetching it."""


class DryRunSink:
    """Synthetic monotonically increasing ids (no database)."""

    def __init__(self) -> None:
        self._next = 1

    def _id(self) -> int:
        i = self._next
        self._next += 1
        return i

    def upsert_html_page(
        self,
        *,
        canonical_url: str,
        fetched_url: str,
        title: str | None,
        parent_source_id: int | None,
    ) -> int:
        return self._id()

    def register_pdf(
        self,
        *,
        canonical_url: str,
        fetched_url: str,
        parent_source_id: int | None,
    ) -> int:
        return self._id()

    def register_html_discovered(
        self,
        *,
        canonical_url: str,
        parent_source_id: int | None,
    ) -> int:
        return self._id()

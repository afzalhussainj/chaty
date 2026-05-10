"""Shared types for the crawler pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


class CrawlMode(str, Enum):
    """How far the engine expands the frontier."""

    full = "full"
    """Recursive internal crawl (BFS) until depth/page limits."""

    single_page = "single_page"
    """Fetch one HTML page; register outgoing links as sources without fetching them."""


LinkKind = Literal["html", "pdf", "other"]


@dataclass(frozen=True, slots=True)
class ParsedLink:
    """A hyperlink extracted from HTML prior to policy filtering."""

    raw_href: str
    absolute_url: str
    kind: LinkKind


@dataclass(frozen=True, slots=True)
class FrontierItem:
    """Work item for the crawl queue."""

    canonical_url: str
    depth: int
    discovered_from_source_id: int | None


@dataclass(slots=True)
class FetchResult:
    """Result of an HTTP fetch (after redirects)."""

    url_requested: str
    final_url: str
    status_code: int
    content_type: str | None
    body: bytes
    redirect_urls: tuple[str, ...] = ()


@dataclass(slots=True)
class CrawlStats:
    """Counters surfaced on the crawl job `stats` JSON field."""

    pages_fetched: int = 0
    pdfs_registered: int = 0
    html_sources_upserted: int = 0
    html_discovered_registered: int = 0
    skipped_robots: int = 0
    skipped_not_allowed: int = 0
    skipped_depth: int = 0
    skipped_max_pages: int = 0
    fetch_errors: int = 0
    sitemap_seeds: int = 0
    touched_source_ids: list[int] = field(default_factory=list)
    extras: dict[str, object] = field(default_factory=dict)


def crawl_stats_to_dict(s: CrawlStats) -> dict[str, object]:
    """Counters + extras for persisting on `CrawlJob.stats` JSON."""
    return {
        "pages_fetched": s.pages_fetched,
        "pdfs_registered": s.pdfs_registered,
        "html_sources_upserted": s.html_sources_upserted,
        "html_discovered_registered": s.html_discovered_registered,
        "skipped_robots": s.skipped_robots,
        "skipped_not_allowed": s.skipped_not_allowed,
        "skipped_depth": s.skipped_depth,
        "skipped_max_pages": s.skipped_max_pages,
        "fetch_errors": s.fetch_errors,
        "sitemap_seeds": s.sitemap_seeds,
        "touched_source_ids": list(s.touched_source_ids),
        **s.extras,
    }


@dataclass(slots=True)
class DryRunRecord:
    """One discovered URL in dry-run mode (no DB writes)."""

    canonical_url: str
    kind: LinkKind
    depth: int
    discovered_from: str | None
    would_register: bool

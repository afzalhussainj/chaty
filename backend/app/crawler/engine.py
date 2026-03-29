"""Orchestrates fetch → parse → enqueue and optional `Source` registration."""

from __future__ import annotations

from dataclasses import dataclass

from app.crawler.discovery import content_type_is_pdf, parse_links_from_href
from app.crawler.fetch import HttpFetcher
from app.crawler.normalization import looks_like_pdf_url, normalize_url
from app.crawler.parse import extract_anchor_hrefs, extract_title
from app.crawler.queue import CrawlFrontier
from app.crawler.robots import RobotsChecker
from app.crawler.rules import CrawlRules
from app.crawler.sink import CrawlSink, DryRunSink
from app.crawler.sitemap import fetch_sitemap_urls
from app.crawler.types import CrawlMode, CrawlStats, DryRunRecord, FrontierItem

ABSOLUTE_MAX_DEPTH = 100
ABSOLUTE_MAX_PAGES = 100_000


def _effective_max_depth(raw: int | None) -> int:
    if raw is None:
        return ABSOLUTE_MAX_DEPTH
    return min(max(0, raw), ABSOLUTE_MAX_DEPTH)


def _effective_max_pages(raw: int | None) -> int:
    if raw is None:
        return ABSOLUTE_MAX_PAGES
    return min(max(1, raw), ABSOLUTE_MAX_PAGES)


def _sniff_html(body: bytes) -> bool:
    head = body[:4096].lower()
    return b"<html" in head or b"<!doctype html" in head


def _sniff_pdf(body: bytes) -> bool:
    return len(body) >= 4 and body[:4] == b"%PDF"


@dataclass(slots=True)
class CrawlRunResult:
    stats: CrawlStats
    dry_run_records: list[DryRunRecord]


class CrawlEngine:
    """
    BFS crawler with duplicate suppression, policy gates, and optional dry-run.

    Playwright / JS rendering: swap `HttpFetcher` for a renderer implementation later.
    """

    def __init__(
        self,
        rules: CrawlRules,
        fetcher: HttpFetcher,
        *,
        mode: CrawlMode,
        max_depth: int | None,
        max_pages: int | None,
        allow_pdf_crawling: bool,
        respect_robots_txt: bool,
        user_agent: str,
        use_sitemap: bool,
        dry_run: bool,
    ) -> None:
        self._rules = rules
        self._fetcher = fetcher
        self._mode = mode
        self._max_depth = _effective_max_depth(max_depth)
        self._max_pages = _effective_max_pages(max_pages)
        self._allow_pdf = allow_pdf_crawling
        self._robots = RobotsChecker(
            enabled=respect_robots_txt,
            user_agent=user_agent,
        )
        self._use_sitemap = use_sitemap
        self._dry_run = dry_run

    def run(
        self,
        seed_urls: list[str],
        sink: CrawlSink | None,
    ) -> CrawlRunResult:
        effective_sink: CrawlSink = sink if sink is not None else DryRunSink()
        stats = CrawlStats()
        dry: list[DryRunRecord] = []

        if self._mode == CrawlMode.single_page:
            if not seed_urls:
                return CrawlRunResult(stats=stats, dry_run_records=dry)
            return self._run_single_page(seed_urls[0], effective_sink, stats, dry)

        frontier = CrawlFrontier()
        self._seed_frontier(frontier, seed_urls, stats)

        if self._use_sitemap:
            try:
                base = seed_urls[0] if seed_urls else ""
                if base:
                    sm = fetch_sitemap_urls(base, self._fetcher)
                    stats.sitemap_seeds = len(sm)
                    for u in sm:
                        if self._rules.allows_url(u):
                            frontier.enqueue(FrontierItem(u, 0, None))
            except OSError:
                stats.extras["sitemap_error"] = "fetch_failed"

        pages = 0
        while len(frontier) > 0:
            if pages >= self._max_pages:
                break
            item = frontier.dequeue()
            if item is None:
                break
            if item.depth > self._max_depth:
                stats.skipped_depth += 1
                continue
            if not self._rules.allows_url(item.canonical_url):
                stats.skipped_not_allowed += 1
                continue
            if not self._robots.allowed(item.canonical_url):
                stats.skipped_robots += 1
                continue

            try:
                fr = self._fetcher.fetch(item.canonical_url)
            except OSError:
                stats.fetch_errors += 1
                continue

            pages += 1
            stats.pages_fetched += 1

            if fr.status_code >= 400:
                stats.fetch_errors += 1
                continue

            try:
                final_canon = normalize_url(fr.final_url)
            except ValueError:
                final_canon = item.canonical_url

            if not self._rules.allows_url(final_canon):
                stats.skipped_not_allowed += 1
                continue

            ct = (fr.content_type or "").lower()
            is_pdf = (
                content_type_is_pdf(fr.content_type)
                or _sniff_pdf(fr.body)
                or (looks_like_pdf_url(final_canon) and not _sniff_html(fr.body))
            )
            if is_pdf:
                if self._allow_pdf:
                    self._record_pdf(
                        effective_sink,
                        final_canon,
                        fr.final_url,
                        item.discovered_from_source_id,
                        stats,
                        dry,
                        item.depth,
                    )
                continue

            if "html" not in ct and "text/" not in ct and not _sniff_html(fr.body):
                continue

            try:
                html = fr.body.decode("utf-8")
            except UnicodeDecodeError:
                html = fr.body.decode("utf-8", errors="replace")

            title = extract_title(html)
            sid = self._record_html_page(
                effective_sink,
                final_canon,
                fr.final_url,
                title,
                item.discovered_from_source_id,
                stats,
                dry,
                item.depth,
            )

            for href in extract_anchor_hrefs(html):
                pl = parse_links_from_href(href, fr.final_url)
                if pl is None or not self._rules.allows_url(pl.absolute_url):
                    if pl is not None:
                        stats.skipped_not_allowed += 1
                    continue
                if pl.kind == "pdf":
                    if self._allow_pdf:
                        self._record_pdf(
                            effective_sink,
                            pl.absolute_url,
                            pl.absolute_url,
                            sid,
                            stats,
                            dry,
                            item.depth + 1,
                        )
                    continue
                if pl.kind != "html":
                    continue
                nd = item.depth + 1
                if nd > self._max_depth:
                    stats.skipped_depth += 1
                    continue
                frontier.enqueue(FrontierItem(pl.absolute_url, nd, sid))

        return CrawlRunResult(stats=stats, dry_run_records=dry)

    def _seed_frontier(
        self,
        frontier: CrawlFrontier,
        seed_urls: list[str],
        stats: CrawlStats,
    ) -> None:
        for raw in seed_urls:
            try:
                c = normalize_url(raw)
            except ValueError:
                continue
            if not self._rules.allows_url(c):
                stats.skipped_not_allowed += 1
                continue
            frontier.enqueue(FrontierItem(c, 0, None))

    def _run_single_page(
        self,
        seed: str,
        sink: CrawlSink,
        stats: CrawlStats,
        dry: list[DryRunRecord],
    ) -> CrawlRunResult:
        try:
            canon = normalize_url(seed)
        except ValueError:
            return CrawlRunResult(stats=stats, dry_run_records=dry)
        if not self._rules.allows_url(canon):
            stats.skipped_not_allowed += 1
            return CrawlRunResult(stats=stats, dry_run_records=dry)
        if not self._robots.allowed(canon):
            stats.skipped_robots += 1
            return CrawlRunResult(stats=stats, dry_run_records=dry)

        try:
            fr = self._fetcher.fetch(canon)
        except OSError:
            stats.fetch_errors += 1
            return CrawlRunResult(stats=stats, dry_run_records=dry)

        stats.pages_fetched += 1
        if fr.status_code >= 400:
            stats.fetch_errors += 1
            return CrawlRunResult(stats=stats, dry_run_records=dry)

        try:
            final_canon = normalize_url(fr.final_url)
        except ValueError:
            final_canon = canon

        if not self._rules.allows_url(final_canon):
            stats.skipped_not_allowed += 1
            return CrawlRunResult(stats=stats, dry_run_records=dry)

        ct = (fr.content_type or "").lower()
        if (
            content_type_is_pdf(fr.content_type)
            or _sniff_pdf(fr.body)
            or (looks_like_pdf_url(final_canon) and not _sniff_html(fr.body))
        ):
            if self._allow_pdf:
                self._record_pdf(sink, final_canon, fr.final_url, None, stats, dry, 0)
            return CrawlRunResult(stats=stats, dry_run_records=dry)

        if "html" not in ct and "text/" not in ct and not _sniff_html(fr.body):
            return CrawlRunResult(stats=stats, dry_run_records=dry)

        try:
            html = fr.body.decode("utf-8")
        except UnicodeDecodeError:
            html = fr.body.decode("utf-8", errors="replace")

        title = extract_title(html)
        sid = self._record_html_page(sink, final_canon, fr.final_url, title, None, stats, dry, 0)

        base = fr.final_url
        for href in extract_anchor_hrefs(html):
            pl = parse_links_from_href(href, base)
            if pl is None or not self._rules.allows_url(pl.absolute_url):
                continue
            if pl.kind == "pdf":
                if self._allow_pdf:
                    self._record_pdf(sink, pl.absolute_url, pl.absolute_url, sid, stats, dry, 1)
                continue
            if pl.kind == "html":
                self._record_html_discovered(sink, pl.absolute_url, sid, stats, dry, 1)

        return CrawlRunResult(stats=stats, dry_run_records=dry)

    def _record_html_page(
        self,
        sink: CrawlSink,
        canonical_url: str,
        fetched_url: str,
        title: str | None,
        parent_id: int | None,
        stats: CrawlStats,
        dry: list[DryRunRecord],
        depth: int,
    ) -> int:
        if self._dry_run:
            dry.append(
                DryRunRecord(
                    canonical_url=canonical_url,
                    kind="html",
                    depth=depth,
                    discovered_from=str(parent_id) if parent_id else None,
                    would_register=True,
                )
            )
        sid = sink.upsert_html_page(
            canonical_url=canonical_url,
            fetched_url=fetched_url,
            title=title,
            parent_source_id=parent_id,
        )
        stats.html_sources_upserted += 1
        return sid

    def _record_pdf(
        self,
        sink: CrawlSink,
        canonical_url: str,
        fetched_url: str,
        parent_id: int | None,
        stats: CrawlStats,
        dry: list[DryRunRecord],
        depth: int,
    ) -> None:
        if self._dry_run:
            dry.append(
                DryRunRecord(
                    canonical_url=canonical_url,
                    kind="pdf",
                    depth=depth,
                    discovered_from=str(parent_id) if parent_id else None,
                    would_register=True,
                )
            )
        sink.register_pdf(
            canonical_url=canonical_url,
            fetched_url=fetched_url,
            parent_source_id=parent_id,
        )
        stats.pdfs_registered += 1

    def _record_html_discovered(
        self,
        sink: CrawlSink,
        canonical_url: str,
        parent_id: int | None,
        stats: CrawlStats,
        dry: list[DryRunRecord],
        depth: int,
    ) -> None:
        if self._dry_run:
            dry.append(
                DryRunRecord(
                    canonical_url=canonical_url,
                    kind="html",
                    depth=depth,
                    discovered_from=str(parent_id) if parent_id else None,
                    would_register=True,
                )
            )
        sink.register_html_discovered(
            canonical_url=canonical_url,
            parent_source_id=parent_id,
        )
        stats.html_discovered_registered += 1

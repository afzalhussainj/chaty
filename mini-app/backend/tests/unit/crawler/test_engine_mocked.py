"""CrawlEngine with an in-memory fetcher (no network)."""

from __future__ import annotations

from types import SimpleNamespace

from app.crawler.engine import CrawlEngine
from app.crawler.fetch import HttpFetcher
from app.crawler.normalization import normalize_url
from app.crawler.rules import CrawlRules
from app.crawler.sink import DryRunSink
from app.crawler.types import CrawlMode, FetchResult


class _MapFetcher:
    def __init__(self, mapping: dict[str, FetchResult]) -> None:
        self._m: dict[str, FetchResult] = {}
        for k, v in mapping.items():
            self._m[normalize_url(k)] = v

    def fetch(self, url: str, *, method: str = "GET") -> FetchResult:
        key = normalize_url(url)
        if key not in self._m:
            msg = f"unexpected fetch {url!r}"
            raise OSError(msg)
        return self._m[key]


def _html(links: list[str]) -> bytes:
    body = "<!doctype html><html><head><title>t</title></head><body>"
    for href in links:
        body += f'<a href="{href}">x</a>'
    body += "</body></html>"
    return body.encode()


def _rules(**kwargs: object) -> CrawlRules:
    cfg = SimpleNamespace(
        base_url=kwargs.get("base_url", "https://ex.com/"),
        allowed_hosts=kwargs.get("allowed_hosts"),
        path_prefixes=kwargs.get("path_prefixes"),
        exclude_globs=kwargs.get("exclude_globs"),
    )
    tenant = SimpleNamespace(allowed_domains=None)
    return CrawlRules.from_config(cfg, tenant)


def test_nested_link_traversal_respects_max_depth() -> None:
    fetcher: HttpFetcher = _MapFetcher(
        {
            "https://ex.com/": FetchResult(
                url_requested="https://ex.com/",
                final_url="https://ex.com/",
                status_code=200,
                content_type="text/html",
                body=_html(["/a"]),
            ),
            "https://ex.com/a": FetchResult(
                url_requested="https://ex.com/a",
                final_url="https://ex.com/a",
                status_code=200,
                content_type="text/html",
                body=_html(["/b"]),
            ),
            "https://ex.com/b": FetchResult(
                url_requested="https://ex.com/b",
                final_url="https://ex.com/b",
                status_code=200,
                content_type="text/html",
                body=_html([]),
            ),
        }
    )
    eng = CrawlEngine(
        _rules(),
        fetcher,
        mode=CrawlMode.full,
        max_depth=1,
        max_pages=50,
        allow_pdf_crawling=True,
        respect_robots_txt=False,
        user_agent="test",
        use_sitemap=False,
        dry_run=True,
    )
    r = eng.run(["https://ex.com/"], DryRunSink())
    assert r.stats.pages_fetched == 2
    assert r.stats.skipped_depth >= 1


def test_duplicate_links_not_fetched_twice() -> None:
    fetcher = _MapFetcher(
        {
            "https://ex.com/": FetchResult(
                url_requested="https://ex.com/",
                final_url="https://ex.com/",
                status_code=200,
                content_type="text/html",
                body=_html(["/same", "/same", "https://ex.com/same"]),
            ),
            "https://ex.com/same": FetchResult(
                url_requested="https://ex.com/same",
                final_url="https://ex.com/same",
                status_code=200,
                content_type="text/html",
                body=_html([]),
            ),
        }
    )
    eng = CrawlEngine(
        _rules(),
        fetcher,
        mode=CrawlMode.full,
        max_depth=3,
        max_pages=10,
        allow_pdf_crawling=True,
        respect_robots_txt=False,
        user_agent="test",
        use_sitemap=False,
        dry_run=True,
    )
    r = eng.run(["https://ex.com/"], DryRunSink())
    assert r.stats.pages_fetched == 2


def test_pdf_link_registered_without_fetching_pdf_bytes() -> None:
    fetcher = _MapFetcher(
        {
            "https://ex.com/": FetchResult(
                url_requested="https://ex.com/",
                final_url="https://ex.com/",
                status_code=200,
                content_type="text/html",
                body=_html(["/doc.pdf"]),
            ),
        }
    )
    eng = CrawlEngine(
        _rules(),
        fetcher,
        mode=CrawlMode.full,
        max_depth=2,
        max_pages=10,
        allow_pdf_crawling=True,
        respect_robots_txt=False,
        user_agent="test",
        use_sitemap=False,
        dry_run=True,
    )
    r = eng.run(["https://ex.com/"], DryRunSink())
    assert r.stats.pages_fetched == 1
    assert r.stats.pdfs_registered == 1


def test_single_page_registers_outgoing_html_without_fetch() -> None:
    fetcher = _MapFetcher(
        {
            "https://ex.com/page": FetchResult(
                url_requested="https://ex.com/page",
                final_url="https://ex.com/page",
                status_code=200,
                content_type="text/html",
                body=_html(["/other"]),
            ),
        }
    )
    eng = CrawlEngine(
        _rules(),
        fetcher,
        mode=CrawlMode.single_page,
        max_depth=0,
        max_pages=1,
        allow_pdf_crawling=True,
        respect_robots_txt=False,
        user_agent="test",
        use_sitemap=False,
        dry_run=True,
    )
    r = eng.run(["https://ex.com/page"], DryRunSink())
    assert r.stats.pages_fetched == 1
    assert r.stats.html_discovered_registered == 1

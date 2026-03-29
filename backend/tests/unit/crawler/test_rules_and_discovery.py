"""CrawlRules and link discovery helpers."""

from __future__ import annotations

from types import SimpleNamespace

from app.crawler.discovery import parse_links_from_href
from app.crawler.rules import CrawlRules


def _rules(
    *,
    base_url: str = "https://example.com/",
    allowed_hosts: list[str] | None = None,
    path_prefixes: list[str] | None = None,
    exclude_globs: list[str] | None = None,
    tenant_domains: list[str] | None = None,
) -> CrawlRules:
    cfg = SimpleNamespace(
        base_url=base_url,
        allowed_hosts=allowed_hosts,
        path_prefixes=path_prefixes,
        exclude_globs=exclude_globs,
    )
    tenant = SimpleNamespace(allowed_domains=tenant_domains)
    return CrawlRules.from_config(cfg, tenant)


def test_host_allowlist_includes_base_and_tenant_domains() -> None:
    r = _rules(tenant_domains=["other.edu"])
    assert r.allows_url("https://example.com/p")
    assert r.allows_url("https://other.edu/p")


def test_path_prefix_include() -> None:
    r = _rules(path_prefixes=["/public"])
    assert r.allows_url("https://example.com/public/x")
    assert not r.allows_url("https://example.com/private/x")


def test_exclude_glob() -> None:
    r = _rules(exclude_globs=["/admin/*"])
    assert not r.allows_url("https://example.com/admin/login")
    assert r.allows_url("https://example.com/public/")


def test_parse_relative_and_normalize() -> None:
    pl = parse_links_from_href("./x", "https://example.com/foo/bar")
    assert pl is not None
    assert pl.absolute_url == "https://example.com/foo/x"
    assert pl.kind == "html"

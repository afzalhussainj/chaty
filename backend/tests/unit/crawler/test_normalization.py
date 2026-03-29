"""URL normalization and PDF heuristics."""

from __future__ import annotations

import pytest
from app.crawler.normalization import looks_like_pdf_url, normalize_url, resolve_url


def test_trailing_slash_duplicates_merge() -> None:
    a = normalize_url("https://example.com/foo/")
    b = normalize_url("https://example.com/foo")
    assert a == b


def test_root_trailing_slash() -> None:
    a = normalize_url("https://example.com/")
    b = normalize_url("https://example.com")
    assert a == b


def test_query_sorted_for_dedup() -> None:
    a = normalize_url("https://example.com/x?b=2&a=1")
    b = normalize_url("https://example.com/x?a=1&b=2")
    assert a == b


def test_fragment_stripped() -> None:
    a = normalize_url("https://example.com/doc#a")
    b = normalize_url("https://example.com/doc#b")
    assert a == b


def test_default_port_removed() -> None:
    a = normalize_url("https://example.com:443/path")
    b = normalize_url("https://example.com/path")
    assert a == b


def test_relative_links_resolved_against_base() -> None:
    base = "https://example.com/a/b/c"
    assert normalize_url("../x", base) == "https://example.com/a/x"
    assert normalize_url("./y", base) == "https://example.com/a/b/y"
    assert normalize_url("/z", base) == "https://example.com/z"


def test_resolve_only() -> None:
    assert resolve_url("foo", "https://example.com/bar/").startswith("https://example.com/bar/foo")


def test_pdf_heuristic() -> None:
    assert looks_like_pdf_url("https://example.com/a/b.PDF")
    assert looks_like_pdf_url("https://example.com/x.pdf?download=1")
    assert not looks_like_pdf_url("https://example.com/pdf-viewer")


def test_path_dot_segments() -> None:
    assert normalize_url("https://example.com/foo/../bar") == "https://example.com/bar"


def test_rejects_non_http_scheme() -> None:
    with pytest.raises(ValueError):
        normalize_url("mailto:a@b.com")

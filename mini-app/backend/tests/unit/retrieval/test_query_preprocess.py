"""Query normalization."""

from __future__ import annotations

from app.retrieval.query_preprocess import fts_query_text, normalize_query


def test_normalize_collapses_whitespace() -> None:
    assert normalize_query("  hello   world  \n", max_chars=100) == "hello world"


def test_normalize_truncates() -> None:
    long = "word " * 2000
    out = normalize_query(long, max_chars=50)
    assert len(out) <= 50


def test_fts_query_passes_through() -> None:
    assert fts_query_text("Tuition fees 2025") == "Tuition fees 2025"

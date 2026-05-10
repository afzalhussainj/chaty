"""Query normalization."""

from __future__ import annotations

from app.retrieval.query_preprocess import fts_query_text, is_smalltalk_query, normalize_query


def test_normalize_collapses_whitespace() -> None:
    assert normalize_query("  hello   world  \n", max_chars=100) == "hello world"


def test_normalize_truncates() -> None:
    long = "word " * 2000
    out = normalize_query(long, max_chars=50)
    assert len(out) <= 50


def test_fts_query_passes_through() -> None:
    assert fts_query_text("Tuition fees 2025") == "Tuition fees 2025"


def test_normalize_corrects_common_vc_typo() -> None:
    out = normalize_query("who is vice chancelloe of uet?", max_chars=200)
    assert "vice chancellor" in out.lower()


def test_smalltalk_detection() -> None:
    assert is_smalltalk_query("hello")
    assert is_smalltalk_query("Assalam o Alaikum")
    assert not is_smalltalk_query("who is the vice chancelloe?")

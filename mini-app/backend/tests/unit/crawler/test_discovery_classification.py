"""PDF vs HTML classification and Content-Type helper."""

from __future__ import annotations

from app.crawler.discovery import classify_url, content_type_is_pdf, parse_links_from_href


def test_classify_pdf_by_extension() -> None:
    assert classify_url("https://ex.edu/doc/a.pdf") == "pdf"


def test_classify_html_url() -> None:
    assert classify_url("https://ex.edu/doc/page") == "html"


def test_parse_links_from_href_marks_pdf_kind() -> None:
    pl = parse_links_from_href("/file.pdf", "https://ex.edu/base/")
    assert pl is not None
    assert pl.kind == "pdf"
    assert pl.absolute_url.endswith("file.pdf")


def test_content_type_is_pdf() -> None:
    assert content_type_is_pdf("application/pdf")
    assert content_type_is_pdf("application/pdf; charset=binary")
    assert not content_type_is_pdf("text/html")
    assert not content_type_is_pdf(None)

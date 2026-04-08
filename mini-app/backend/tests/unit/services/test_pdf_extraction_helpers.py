"""PDF extraction hashing, joining, and idempotency helpers."""

from __future__ import annotations

from app.extractors.pdf_protocol import PdfExtractionResult, PdfPage
from app.services.pdf_extraction_service import (
    _join_pages_full_text,
    _pdf_extraction_hash,
)


def test_extraction_hash_stable_for_same_structure() -> None:
    pages = (PdfPage(1, "a"), PdfPage(2, "b"))
    r = PdfExtractionResult(
        pages=pages,
        page_count=2,
        extractor_id="pymupdf",
        extractor_version="1.0",
    )
    h1 = _pdf_extraction_hash(r)
    h2 = _pdf_extraction_hash(r)
    assert h1 == h2


def test_extraction_hash_changes_when_page_text_changes() -> None:
    r1 = PdfExtractionResult(
        pages=(PdfPage(1, "same"),),
        page_count=1,
        extractor_id="pymupdf",
        extractor_version="1.0",
    )
    r2 = PdfExtractionResult(
        pages=(PdfPage(1, "different"),),
        page_count=1,
        extractor_id="pymupdf",
        extractor_version="1.0",
    )
    assert _pdf_extraction_hash(r1) != _pdf_extraction_hash(r2)


def test_join_pages_preserves_markers() -> None:
    pages = (PdfPage(1, "A"), PdfPage(2, "B"))
    s = _join_pages_full_text(pages)
    assert "[[PAGE 1]]" in s
    assert "[[PAGE 2]]" in s
    assert "A" in s and "B" in s


def test_reprocess_same_content_same_fingerprint() -> None:
    """Simulates unchanged PDF bytes → same structured extraction → same hash."""
    r = PdfExtractionResult(
        pages=(PdfPage(1, "x"), PdfPage(2, "y")),
        page_count=2,
        extractor_id="pymupdf",
        extractor_version="9",
    )
    assert _pdf_extraction_hash(r) == _pdf_extraction_hash(r)


def test_file_name_from_url() -> None:
    from app.services.pdf_extraction_service import _file_name_from_url

    assert _file_name_from_url("https://host.edu/path/My%20Doc.pdf") == "My Doc.pdf"

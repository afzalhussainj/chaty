"""Unit tests for heading / page-aware chunking (no database)."""

from __future__ import annotations

from app.indexing.chunker import chunk_extracted_document
from app.models.extracted import ExtractedDocument


def _doc(
    *,
    full_text: str,
    meta: dict | None = None,
    page_count: int | None = 1,
    kind: str | None = None,
) -> ExtractedDocument:
    m = dict(meta or {})
    if kind:
        m["kind"] = kind
    return ExtractedDocument(
        id=1,
        tenant_id=1,
        source_id=1,
        source_snapshot_id=1,
        extraction_hash="h1",
        full_text=full_text,
        page_count=page_count,
        extraction_metadata=m,
    )


def test_markdown_heading_splits_sections() -> None:
    text = """# Title ignored in sections sometimes
Intro para.

## Section A
Alpha content here.

## Section B
Beta content here.
"""
    doc = _doc(full_text=text, meta={"headings": []})
    chunks = chunk_extracted_document(doc)
    headings = {c.heading for c in chunks}
    assert "Section A" in headings
    assert "Section B" in headings
    assert all(c.page_number is None for c in chunks)


def test_chunk_boundaries_respect_max_size() -> None:
    body = "word " * 2000
    text = f"## Part\n{body}"
    doc = _doc(full_text=text, meta={"headings": []})
    chunks = chunk_extracted_document(doc, max_chunk_chars=400, overlap_chars=40)
    assert len(chunks) >= 3
    assert all(len(c.content) <= 400 for c in chunks)
    assert chunks[0].heading == "Part"


def test_pdf_page_markers_set_page_number() -> None:
    text = """[[PAGE 1]]
Short p1.

[[PAGE 2]]
This is page two with more text.
[[PAGE 3]]
Final page."""
    doc = _doc(full_text=text, kind="pdf", page_count=3)
    chunks = chunk_extracted_document(doc, max_chunk_chars=500)
    pages = [c.page_number for c in chunks]
    assert 1 in pages
    assert 2 in pages
    assert 3 in pages
    assert all(c.heading is None for c in chunks)


def test_pdf_long_page_subchunked() -> None:
    filler = "x" * 800
    text = f"[[PAGE 5]]\n{filler}\n{filler}"
    doc = _doc(full_text=text, kind="pdf", page_count=1)
    chunks = chunk_extracted_document(doc, max_chunk_chars=900, overlap_chars=50)
    assert len(chunks) >= 2
    assert all(c.page_number == 5 for c in chunks)

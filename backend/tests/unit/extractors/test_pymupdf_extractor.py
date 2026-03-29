"""PyMuPDF PDF extraction (multi-page, page numbers)."""

from __future__ import annotations

import pytest

pytest.importorskip("fitz", reason="PyMuPDF not installed")

import fitz
from app.extractors.pymupdf_extractor import PyMuPdfExtractor


def _build_pdf_bytes() -> bytes:
    doc = fitz.open()
    try:
        for i in range(3):
            page = doc.new_page()
            page.insert_text((72, 72), f"Page {i + 1} content")
        return doc.tobytes()
    finally:
        doc.close()


def test_multipage_extraction_preserves_page_numbers() -> None:
    raw = _build_pdf_bytes()
    ext = PyMuPdfExtractor()
    r = ext.extract(raw, file_name="t.pdf")
    assert r.page_count == 3
    assert [p.page_number for p in r.pages] == [1, 2, 3]
    for i, p in enumerate(r.pages, start=1):
        assert f"Page {i}" in p.text


def test_text_per_page_not_merged() -> None:
    raw = _build_pdf_bytes()
    r = PyMuPdfExtractor().extract(raw, file_name="x.pdf")
    assert "Page 1" in r.pages[0].text
    assert "Page 3" not in r.pages[0].text

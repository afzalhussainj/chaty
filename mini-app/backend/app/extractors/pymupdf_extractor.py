"""PyMuPDF (fitz) PDF text extraction."""

from __future__ import annotations

import fitz

from app.extractors.pdf_protocol import PdfExtractionResult, PdfPage

# Prefer package version when available
try:
    import importlib.metadata as _im

    _VER = _im.version("PyMuPDF")
except Exception:  # noqa: BLE001
    _VER = "unknown"


class PyMuPdfExtractor:
    """Default PDF extractor: one text block per page, 1-based page indices."""

    @property
    def id(self) -> str:
        return "pymupdf"

    @property
    def version(self) -> str:
        return _VER

    def extract(self, pdf_bytes: bytes, *, file_name: str) -> PdfExtractionResult:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        try:
            pages: list[PdfPage] = []
            for i in range(doc.page_count):
                page = doc[i]
                text = (page.get_text("text") or "").strip()
                pages.append(PdfPage(page_number=i + 1, text=text))
        finally:
            doc.close()
        return PdfExtractionResult(
            pages=tuple(pages),
            page_count=len(pages),
            extractor_id=self.id,
            extractor_version=self.version,
            language=None,
        )

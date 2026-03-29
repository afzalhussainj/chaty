"""PDF extraction interface (bytes in, structured pages out; no HTTP or DB)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class PdfPage:
    """One PDF page (1-based page numbers for citations)."""

    page_number: int
    text: str


@dataclass(frozen=True, slots=True)
class PdfExtractionResult:
    """Deterministic output from a PDF binary."""

    pages: tuple[PdfPage, ...]
    page_count: int
    extractor_id: str
    extractor_version: str
    language: str | None = None


@runtime_checkable
class PdfExtractor(Protocol):
    """Pluggable PDF backend (PyMuPDF today; swap for cloud OCR later)."""

    @property
    def id(self) -> str:
        """Stable id stored in `ExtractedDocument.extraction_metadata`."""

    @property
    def version(self) -> str:
        """Version string for extraction_hash / provenance."""

    def extract(self, pdf_bytes: bytes, *, file_name: str) -> PdfExtractionResult:
        """Extract page-by-page plain text."""

"""Fetch PDF bytes for a `Source`, run `PdfExtractor`, persist snapshot + `ExtractedDocument`."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.settings import get_settings
from app.extractors.pdf_protocol import PdfExtractionResult, PdfExtractor, PdfPage
from app.extractors.pymupdf_extractor import PyMuPdfExtractor
from app.models.enums import SourceStatus, SourceType
from app.models.extracted import DocumentChunk, ExtractedDocument
from app.models.source import Source, SourceSnapshot
from app.repositories.extracted_document import ExtractedDocumentRepository
from app.repositories.source_snapshot import SourceSnapshotRepository

_DEFAULT_PDF_EXTRACTOR: PyMuPdfExtractor | None = None


def get_default_pdf_extractor() -> PyMuPdfExtractor:
    global _DEFAULT_PDF_EXTRACTOR
    if _DEFAULT_PDF_EXTRACTOR is None:
        _DEFAULT_PDF_EXTRACTOR = PyMuPdfExtractor()
    return _DEFAULT_PDF_EXTRACTOR


def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _pdf_extraction_hash(result: PdfExtractionResult) -> str:
    """Hash structured page texts + extractor identity (deterministic)."""
    lines = [f"{p.page_number}\t{p.text}" for p in result.pages]
    payload = f"{result.extractor_id}\n{result.extractor_version}\n" + "\n".join(lines)
    return _sha256_hex(payload)


def _file_name_from_url(url: str) -> str:
    from urllib.parse import unquote, urlparse

    path = unquote(urlparse(url).path or "")
    base = path.rsplit("/", 1)[-1].strip() or "document.pdf"
    if not base.lower().endswith(".pdf"):
        base = f"{base}.pdf"
    return base


def _file_name_from_content_disposition(value: str | None) -> str | None:
    if not value:
        return None
    m = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', value, re.I)
    if m:
        return m.group(1).strip()
    return None


def _join_pages_full_text(pages: tuple[PdfPage, ...]) -> str:
    """Human-readable full text with explicit page markers (chunking can split on these)."""
    parts: list[str] = []
    for p in pages:
        parts.append(f"[[PAGE {p.page_number}]]\n{p.text}")
    return "\n\n".join(parts)


def _build_pdf_metadata(
    source: Source,
    result: PdfExtractionResult,
    *,
    file_name: str,
    fetched_url: str,
    raw_hash: str,
    extraction_status: str,
) -> dict[str, Any]:
    return {
        "kind": "pdf",
        "file_name": file_name,
        "source_url": source.url,
        "canonical_url": source.canonical_url,
        "fetched_url": fetched_url,
        "extraction_status": extraction_status,
        "raw_content_hash": raw_hash,
        "page_count": result.page_count,
        "pages": [{"page_number": p.page_number, "text": p.text} for p in result.pages],
        "extractor": {"id": result.extractor_id, "version": result.extractor_version},
    }


def _http_get_pdf(url: str, user_agent: str) -> httpx.Response:
    with httpx.Client(follow_redirects=True, timeout=120.0) as client:
        return client.get(url, headers={"User-Agent": user_agent})


def _delete_chunks(session: Session, extracted_document_id: int) -> None:
    session.execute(
        delete(DocumentChunk).where(DocumentChunk.extracted_document_id == extracted_document_id),
    )


def extract_pdf_source(
    session: Session,
    source_id: int,
    *,
    tenant_id: int | None = None,
    force: bool = False,
    extractor: PdfExtractor | None = None,
) -> ExtractedDocument:
    """
    Download PDF bytes, extract page-by-page, store structured metadata + `full_text`.

    Skips work when raw bytes match the latest snapshot and an `ExtractedDocument` exists,
    unless ``force`` is True.
    """
    source = session.get(Source, source_id)
    if source is None:
        msg = "Source not found"
        raise ValueError(msg)
    if tenant_id is not None and source.tenant_id != tenant_id:
        msg = "Source does not belong to tenant"
        raise ValueError(msg)
    if source.source_type != SourceType.pdf:
        msg = "PDF extraction is only supported for pdf sources"
        raise ValueError(msg)

    settings = get_settings()
    ua = f"{settings.app_name}/pdf-extractor"
    ext = extractor or get_default_pdf_extractor()

    resp = _http_get_pdf(source.url, ua)
    if resp.status_code == 404:
        source.is_active = False
        source.deactivated_at = datetime.now(timezone.utc)
        session.flush()
    if resp.status_code >= 400:
        source.status = SourceStatus.extraction_failed
        session.flush()
        msg = f"HTTP {resp.status_code} fetching PDF URL"
        raise ValueError(msg)
    body = resp.content
    final_url = str(resp.url)
    cd_name = _file_name_from_content_disposition(resp.headers.get("content-disposition"))
    file_name = cd_name or _file_name_from_url(final_url)

    raw_hash = _sha256_bytes(body)
    snap_repo = SourceSnapshotRepository(session)
    ex_repo = ExtractedDocumentRepository(session)
    latest = snap_repo.latest_for_source(source_id)
    need_new_snapshot = latest is None or latest.raw_content_hash != raw_hash

    if need_new_snapshot:
        ver = snap_repo.next_version(source_id)
        snapshot = SourceSnapshot(
            source_id=source_id,
            version=ver,
            raw_content_hash=raw_hash,
            byte_length=len(body),
            mime_type="application/pdf",
            storage_uri=None,
        )
        snap_repo.add(snapshot)
    else:
        snapshot = latest

    if not need_new_snapshot and not force:
        existing_doc = ex_repo.get_by_snapshot_id(snapshot.id)
        if existing_doc is not None:
            source.status = SourceStatus.ready_to_index
            session.flush()
            return existing_doc

    try:
        result = ext.extract(body, file_name=file_name)
    except Exception as exc:  # noqa: BLE001 — PyMuPDF errors
        source.status = SourceStatus.extraction_failed
        session.flush()
        msg = f"PDF extraction failed: {exc}"
        raise ValueError(msg) from exc

    full_text = _join_pages_full_text(result.pages)
    meta = _build_pdf_metadata(
        source,
        result,
        file_name=file_name,
        fetched_url=final_url,
        raw_hash=raw_hash,
        extraction_status="complete",
    )
    exh = _pdf_extraction_hash(result)
    title = source.title or file_name.rsplit(".", 1)[0]

    existing = ex_repo.get_by_snapshot_id(snapshot.id)
    if existing is not None:
        _delete_chunks(session, existing.id)
        existing.title = title
        existing.language = result.language
        existing.full_text = full_text
        existing.page_count = result.page_count
        existing.extraction_hash = exh
        existing.extraction_metadata = meta
        source.content_hash = raw_hash
        source.status = SourceStatus.ready_to_index
        session.flush()
        return existing

    doc = ExtractedDocument(
        tenant_id=source.tenant_id,
        source_id=source_id,
        source_snapshot_id=snapshot.id,
        extraction_hash=exh,
        title=title,
        language=result.language,
        full_text=full_text,
        page_count=result.page_count,
        extraction_metadata=meta,
    )
    ex_repo.add(doc)
    source.content_hash = raw_hash
    source.status = SourceStatus.ready_to_index
    session.flush()
    return doc

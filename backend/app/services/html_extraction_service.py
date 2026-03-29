"""Fetch HTML for a `Source`, run an extractor, persist snapshot + extracted document."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.http_retries import httpx_get_with_retry
from app.core.settings import get_settings
from app.extractors.clutter import strip_clutter_html
from app.extractors.protocol import ExtractorChain, HtmlExtractionResult, HtmlExtractor
from app.extractors.trafilatura_extractor import TrafilaturaHtmlExtractor
from app.models.enums import SourceStatus, SourceType
from app.models.extracted import DocumentChunk, ExtractedDocument
from app.models.source import Source, SourceSnapshot
from app.repositories.extracted_document import ExtractedDocumentRepository
from app.repositories.source_snapshot import SourceSnapshotRepository

_DEFAULT_EXTRACTOR: ExtractorChain | None = None


def get_default_html_extractor() -> ExtractorChain:
    """Clutter strip + trafilatura Markdown extraction."""
    global _DEFAULT_EXTRACTOR
    if _DEFAULT_EXTRACTOR is None:
        _DEFAULT_EXTRACTOR = ExtractorChain(
            preprocessors=(strip_clutter_html,),
            extractor=TrafilaturaHtmlExtractor(),
        )
    return _DEFAULT_EXTRACTOR


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _extraction_hash(result: HtmlExtractionResult) -> str:
    payload = f"{result.extractor_id}\n{result.extractor_version}\n{result.format}\n{result.text}"
    return _sha256_hex(payload)


def _build_metadata(source: Source, result: HtmlExtractionResult, final_url: str) -> dict[str, Any]:
    return {
        "source_url": source.url,
        "canonical_url": source.canonical_url,
        "fetched_url": final_url,
        "output_format": result.format,
        "extractor": {"id": result.extractor_id, "version": result.extractor_version},
        "headings": [{"level": h.level, "text": h.text} for h in result.headings[:500]],
    }


def _http_get(url: str, user_agent: str) -> httpx.Response:
    s = get_settings()
    return httpx_get_with_retry(
        url,
        user_agent=user_agent,
        timeout_s=s.extraction_http_timeout_s,
        max_retries=s.extraction_http_max_retries,
        backoff_s=s.crawl_http_retry_backoff_s,
    )


def _delete_chunks(session: Session, extracted_document_id: int) -> None:
    session.execute(
        delete(DocumentChunk).where(DocumentChunk.extracted_document_id == extracted_document_id),
    )


def extract_html_source(
    session: Session,
    source_id: int,
    *,
    tenant_id: int | None = None,
    force: bool = False,
    extractor: HtmlExtractor | None = None,
) -> ExtractedDocument:
    """
    Download HTML for `source_id`, run extractor, write snapshot + `ExtractedDocument`.

    Idempotent when raw bytes match the latest snapshot unless ``force`` (re-run extractor).
    """
    source = session.get(Source, source_id)
    if source is None:
        msg = "Source not found"
        raise ValueError(msg)
    if tenant_id is not None and source.tenant_id != tenant_id:
        msg = "Source does not belong to tenant"
        raise ValueError(msg)
    if source.source_type != SourceType.html_page:
        msg = "Extraction is only supported for html_page sources"
        raise ValueError(msg)

    settings = get_settings()
    ua = f"{settings.app_name}/extractor"
    ext = extractor or get_default_html_extractor()

    resp = _http_get(source.url, ua)
    if resp.status_code == 404:
        source.is_active = False
        source.deactivated_at = datetime.now(timezone.utc)
        session.flush()
    if resp.status_code >= 400:
        source.status = SourceStatus.extraction_failed
        session.flush()
        msg = f"HTTP {resp.status_code} fetching source URL"
        raise ValueError(msg)
    body = resp.content
    final_url = str(resp.url)
    raw_hash = _sha256_bytes(body)
    html = body.decode("utf-8", errors="replace")

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
            mime_type="text/html",
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

    result = ext.extract(html, source_url=final_url)

    title = result.title or source.title
    meta = _build_metadata(source, result, final_url)
    exh = _extraction_hash(result)

    existing = ex_repo.get_by_snapshot_id(snapshot.id)
    if existing is not None:
        _delete_chunks(session, existing.id)
        existing.title = title
        existing.language = result.language
        existing.full_text = result.text
        existing.page_count = 1
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
        full_text=result.text,
        page_count=1,
        extraction_metadata=meta,
    )
    ex_repo.add(doc)
    source.content_hash = raw_hash
    source.status = SourceStatus.ready_to_index
    session.flush()
    return doc

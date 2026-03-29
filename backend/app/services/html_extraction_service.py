"""Fetch HTML for a `Source`, run an extractor, persist snapshot + extracted document."""

from __future__ import annotations

import hashlib
from typing import Any

import httpx
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.settings import get_settings
from app.extractors.clutter import strip_clutter_html
from app.extractors.protocol import ExtractorChain, HtmlExtractionResult, HtmlExtractor
from app.extractors.trafilatura_extractor import TrafilaturaHtmlExtractor
from app.models.enums import JobStatus, SourceStatus, SourceType
from app.models.extracted import DocumentChunk, ExtractedDocument
from app.models.job import CrawlJob
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


def _fetch_html(url: str, user_agent: str) -> tuple[bytes, str]:
    with httpx.Client(follow_redirects=True, timeout=45.0) as client:
        resp = client.get(url, headers={"User-Agent": user_agent})
        if resp.status_code >= 400:
            msg = f"HTTP {resp.status_code} fetching source URL"
            raise ValueError(msg)
        return resp.content, str(resp.url)


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

    try:
        body, final_url = _fetch_html(source.url, ua)
    except ValueError:
        source.status = SourceStatus.extraction_failed
        session.flush()
        raise
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


def queue_extractions_after_crawl_job(job_id: int) -> int:
    """
    Enqueue Celery extraction tasks for HTML sources touched by a completed crawl job.

    Returns the number of tasks scheduled. No-op if job missing, not succeeded, or dry-run.
    """
    from app.db.session import SessionLocal, get_engine
    from app.workers.tasks.extract import extract_html_source_task

    session = SessionLocal(bind=get_engine())
    try:
        job = session.get(CrawlJob, job_id)
        if job is None or job.status != JobStatus.succeeded:
            return 0
        stats = job.stats or {}
        if stats.get("dry_run"):
            return 0
        if job.crawl_config_id is None:
            return 0

        stmt = (
            select(Source.id)
            .where(
                Source.tenant_id == job.tenant_id,
                Source.crawl_config_id == job.crawl_config_id,
                Source.source_type == SourceType.html_page,
                Source.last_crawled_at.isnot(None),
            )
        )
        if job.started_at is not None:
            stmt = stmt.where(Source.last_crawled_at >= job.started_at)

        ids = list(session.scalars(stmt))
        for sid in ids:
            extract_html_source_task.delay(int(sid))
        return len(ids)
    finally:
        session.close()

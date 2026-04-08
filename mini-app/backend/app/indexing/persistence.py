"""Replace document chunks in one transaction (idempotent re-index)."""

from __future__ import annotations

import hashlib
from typing import Any

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.extracted import DocumentChunk, ExtractedDocument
from app.models.source import Source


def content_hash_hex(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def delete_chunks_for_document(session: Session, extracted_document_id: int) -> None:
    session.execute(
        delete(DocumentChunk).where(DocumentChunk.extracted_document_id == extracted_document_id),
    )


def resolve_source_url(doc: ExtractedDocument, source: Source) -> str:
    raw = doc.extraction_metadata
    meta: dict[str, Any] = raw if isinstance(raw, dict) else {}
    return str(
        meta.get("fetched_url")
        or meta.get("canonical_url")
        or meta.get("source_url")
        or source.url,
    )


def resolve_title(doc: ExtractedDocument, source: Source) -> str | None:
    return doc.title or source.title


def replace_chunks(
    session: Session,
    *,
    doc: ExtractedDocument,
    source: Source,
    chunk_texts: list[str],
    headings: list[str | None],
    page_numbers: list[int | None],
    embeddings: list[list[float]],
) -> list[DocumentChunk]:
    """
    Delete existing chunks for `doc` and insert new rows. Caller must commit.

    `chunk_texts`, `headings`, `page_numbers`, and `embeddings` must have equal length.
    """
    if not (len(chunk_texts) == len(headings) == len(page_numbers) == len(embeddings)):
        msg = "Chunk lists must have equal length"
        raise ValueError(msg)

    delete_chunks_for_document(session, doc.id)

    source_url = resolve_source_url(doc, source)
    title = resolve_title(doc, source)

    rows: list[DocumentChunk] = []
    for idx, (text, heading, page, emb) in enumerate(
        zip(chunk_texts, headings, page_numbers, embeddings, strict=True),
    ):
        rows.append(
            DocumentChunk(
                tenant_id=doc.tenant_id,
                source_id=doc.source_id,
                extracted_document_id=doc.id,
                chunk_index=idx,
                source_url=source_url,
                title=title,
                heading=heading,
                page_number=page,
                content=text,
                content_hash=content_hash_hex(text),
                embedding=emb,
            ),
        )
    session.add_all(rows)
    session.flush()
    return rows

"""Heading-aware chunking for HTML (markdown) and PDF (page markers)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.models.extracted import ExtractedDocument

# Practical for retrieval (~500–800 tokens); overlap preserves boundary context.
DEFAULT_MAX_CHUNK_CHARS = 2000
DEFAULT_OVERLAP_CHARS = 200

_PAGE_MARKER = re.compile(r"\[\[PAGE\s+(\d+)\]\]\s*", re.IGNORECASE)
_MD_HEADING = re.compile(r"^(#{1,6})\s+(.+)$")


@dataclass(frozen=True, slots=True)
class ChunkDraft:
    """One logical chunk before embedding and persistence."""

    content: str
    heading: str | None
    page_number: int | None


def _strip_or_none(s: str | None) -> str | None:
    if s is None:
        return None
    t = s.strip()
    return t or None


def _subchunk_text(text: str, max_chars: int, overlap: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]
    out: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + max_chars, n)
        out.append(text[start:end])
        if end >= n:
            break
        start = max(0, end - overlap)
    return out


def _split_markdown_sections(full_text: str) -> list[tuple[str | None, str]]:
    """Split on markdown heading lines; first segment may have no heading."""
    lines = full_text.splitlines()
    sections: list[tuple[str | None, list[str]]] = []
    current_heading: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_heading, current_lines
        body = "\n".join(current_lines).strip()
        if current_heading is not None or body:
            sections.append((current_heading, body))
        current_heading = None
        current_lines = []

    for line in lines:
        m = _MD_HEADING.match(line.rstrip())
        if m:
            flush()
            current_heading = m.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)
    flush()
    return [(h, b) for h, b in sections if b]


def _outline_split_sections(
    full_text: str,
    headings: list[dict[str, Any]],
) -> list[tuple[str | None, str]] | None:
    """
    If extraction provided a heading outline, split `full_text` by first occurrences
    of each heading text (in order). Falls back to None if headings missing or not found.
    """
    if not headings:
        return None
    texts = [str(h.get("text") or "").strip() for h in headings if h.get("text")]
    texts = [t for t in texts if t]
    if len(texts) < 2:
        return None
    positions: list[tuple[str, int]] = []
    for t in texts:
        idx = full_text.find(t)
        if idx < 0:
            return None
        positions.append((t, idx))
    positions.sort(key=lambda x: x[1])
    for i in range(len(positions) - 1):
        if positions[i][1] >= positions[i + 1][1]:
            return None
    sections: list[tuple[str | None, str]] = []
    for i, (heading_text, start) in enumerate(positions):
        end = positions[i + 1][1] if i + 1 < len(positions) else len(full_text)
        body = full_text[start:end].strip()
        if heading_text in body:
            body = body.replace(heading_text, "", 1).strip()
        sections.append((heading_text, body))
    preamble_end = positions[0][1]
    if preamble_end > 0:
        pre = full_text[:preamble_end].strip()
        if pre:
            sections.insert(0, (None, pre))
    return sections if sections else None


def _chunk_html_like(
    full_text: str,
    metadata: dict[str, Any],
    *,
    max_chars: int,
    overlap: int,
) -> list[ChunkDraft]:
    meta = metadata or {}
    outline = meta.get("headings")
    sections: list[tuple[str | None, str]] | None = None
    if isinstance(outline, list):
        sections = _outline_split_sections(full_text, outline)
    if not sections:
        sections = _split_markdown_sections(full_text)
    if not sections:
        return []

    out: list[ChunkDraft] = []
    for heading, body in sections:
        h = _strip_or_none(heading)
        for piece in _subchunk_text(body, max_chars, overlap):
            out.append(ChunkDraft(content=piece, heading=h, page_number=None))
    return out


def _pdf_page_segments(full_text: str) -> list[tuple[int, str]]:
    matches = list(_PAGE_MARKER.finditer(full_text))
    if not matches:
        t = full_text.strip()
        return [(1, t)] if t else []

    segments: list[tuple[int, str]] = []
    first = matches[0]
    if first.start() > 0:
        pre = full_text[: first.start()].strip()
        if pre:
            segments.append((1, pre))

    for i, m in enumerate(matches):
        page = int(m.group(1))
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        body = full_text[m.end() : end].strip()
        if body:
            segments.append((page, body))
    return segments


def _chunk_pdf(
    full_text: str,
    *,
    max_chars: int,
    overlap: int,
) -> list[ChunkDraft]:
    out: list[ChunkDraft] = []
    for page_num, body in _pdf_page_segments(full_text):
        for piece in _subchunk_text(body, max_chars, overlap):
            out.append(ChunkDraft(content=piece, heading=None, page_number=page_num))
    return out


def chunk_extracted_document(
    doc: ExtractedDocument,
    *,
    max_chunk_chars: int = DEFAULT_MAX_CHUNK_CHARS,
    overlap_chars: int = DEFAULT_OVERLAP_CHARS,
) -> list[ChunkDraft]:
    """
    Build chunk drafts from stored extraction. PDFs use [[PAGE n]] markers; HTML uses
    heading outline (when reliable) or markdown headings in `full_text`.
    """
    full_text = doc.full_text or ""
    meta = doc.extraction_metadata if isinstance(doc.extraction_metadata, dict) else {}
    is_pdf = meta.get("kind") == "pdf" or (
        "[[PAGE" in full_text and (doc.page_count or 0) > 1
    )

    if is_pdf:
        return _chunk_pdf(full_text, max_chars=max_chunk_chars, overlap=overlap_chars)
    return _chunk_html_like(
        full_text,
        meta,
        max_chars=max_chunk_chars,
        overlap=overlap_chars,
    )

"""Context escaping and citation formatting."""

from __future__ import annotations

from datetime import datetime, timezone

from app.chat.context_formatter import build_user_message, format_context_blocks
from app.chat.citation_formatter import citations_for_display
from app.models.enums import SourceType
from app.retrieval.types import RetrievedChunk


def _chunk(
    cid: int,
    *,
    title: str,
    url: str,
    st: SourceType,
    page: int | None,
    content: str,
    score: float = 0.9,
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=cid,
        content=content,
        score=score,
        vector_score_norm=0.5,
        fts_score_norm=0.5,
        source_id=1,
        source_type=st,
        extracted_document_id=10,
        title=title,
        heading=None,
        page_number=page,
        source_url=url,
        content_hash="h",
        indexed_at=datetime.now(timezone.utc),
    )


def test_context_escapes_injection_chars() -> None:
    ch = _chunk(1, title='"><script>', url="https://x", st=SourceType.html_page, page=None, content="ignore <exec>")
    block, m = format_context_blocks((ch,))
    assert "<script>" not in block
    assert "&lt;" in block


def test_citations_include_pdf_page() -> None:
    ch = _chunk(
        2,
        title="Handbook",
        url="https://x/a.pdf",
        st=SourceType.pdf,
        page=3,
        content="fee",
    )
    cites = citations_for_display(
        chunks_by_index={1: ch},
        cited_indices=[1],
        fallback_chunks=(ch,),
    )
    assert cites[0].page_number == 3
    assert cites[0].source_type == SourceType.pdf


def test_user_message_contains_no_raw_system_prompt() -> None:
    u = build_user_message(user_question="hi", context_block="", answer_mode="concise")
    assert "instructions" not in u.lower()
    assert "CONTEXT" in u

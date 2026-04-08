"""Format retrieved chunks for the model (untrusted input hardening)."""

from __future__ import annotations

import re

from app.retrieval.types import RetrievedChunk

_ZW_RE = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060-\u206f]")


def _sanitize_user_question(text: str) -> str:
    """Strip control / obfuscation characters before escaping (prompt-injection hygiene)."""
    t = "".join(ch for ch in text if ord(ch) >= 32 or ch in "\n\t\r")
    t = _ZW_RE.sub("", t)
    return t.strip()


def _escape_context_text(text: str) -> str:
    """Reduce prompt-injection surface when embedding third-party HTML/Markdown."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def format_context_blocks(
    chunks: tuple[RetrievedChunk, ...],
) -> tuple[str, dict[int, RetrievedChunk]]:
    """
    Build numbered CONTEXT blocks and a 1-based index map.

    Returns (full_text_for_user_message, index_to_chunk).
    """
    if not chunks:
        return "", {}

    parts: list[str] = []
    mapping: dict[int, RetrievedChunk] = {}
    for i, ch in enumerate(chunks, start=1):
        mapping[i] = ch
        title = _escape_context_text(ch.title or "(no title)")
        url = _escape_context_text(ch.source_url or "")
        st = ch.source_type.value
        page = f"page {ch.page_number}" if ch.page_number is not None else "n/a"
        body = _escape_context_text(ch.content)
        heading = _escape_context_text(ch.heading) if ch.heading else ""
        head_line = f"Heading: {heading}\n" if heading else ""
        parts.append(
            f"[{i}] title={title}\n"
            f"url={url}\n"
            f"source_type={st}\n"
            f"pdf_page={page}\n"
            f"{head_line}"
            f"content:\n{body}",
        )
    return "\n\n---\n\n".join(parts), mapping


def build_user_message(
    *,
    user_question: str,
    context_block: str,
    answer_mode: str,
) -> str:
    """Single user turn combining mode, question, and CONTEXT (instructions stay separate)."""
    q = _escape_context_text(_sanitize_user_question(user_question))
    mode = "concise" if answer_mode == "concise" else "detailed"
    if not context_block.strip():
        return (
            f"Answer mode: {mode}\n\n"
            "CONTEXT: (empty — no indexed passages retrieved.)\n\n"
            f"USER QUESTION:\n{q}\n\n"
            "Respond with JSON only per schema."
        )
    return (
        f"Answer mode: {mode}\n\n"
        "CONTEXT (numbered blocks; cite with [n]):\n"
        f"{context_block}\n\n"
        f"USER QUESTION:\n{q}\n\n"
        "Respond with JSON only per schema."
    )

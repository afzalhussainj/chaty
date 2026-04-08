"""Normalize user queries before embedding / FTS."""

from __future__ import annotations

import re

_WS = re.compile(r"\s+")


def normalize_query(raw: str, *, max_chars: int) -> str:
    """Trim, collapse whitespace, cap length for embedding APIs."""
    t = raw.strip()
    t = _WS.sub(" ", t)
    if len(t) > max_chars:
        t = t[:max_chars].rsplit(" ", 1)[0].strip() or t[:max_chars]
    return t


def fts_query_text(normalized: str) -> str:
    """Plain text for `plainto_tsquery` (lexeme extraction happens in PostgreSQL)."""
    return normalized

"""Normalize user queries before embedding / FTS."""

from __future__ import annotations

import re

_WS = re.compile(r"\s+")
_NON_ALNUM = re.compile(r"[^a-z0-9\s]")

# Common misspellings / shorthand that hurt retrieval quality.
_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (r"\bvice[\s-]*chancelloe\b", "vice chancellor"),
    (r"\bvice[\s-]*chancellopr\b", "vice chancellor"),
    (r"\bvice[\s-]*chancellor\b", "vice chancellor"),
    (r"\bvice[\s-]*chancelor\b", "vice chancellor"),
    (r"\bvc\b", "vice chancellor"),
    (r"\bib&m\b", "institute of business and management"),
    (r"\bibm\b", "institute of business and management"),
)

_GREETING_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*(hi|hello|hey|salam|aoa|assalam[ -]?o[ -]?alaikum)\s*[.!?]*\s*$", re.I),
    re.compile(r"^\s*(how are you|kya haal|kaise ho|kesy ho)\s*[.!?]*\s*$", re.I),
)


def normalize_query(raw: str, *, max_chars: int) -> str:
    """Trim, collapse whitespace, cap length for embedding APIs."""
    t = raw.strip()
    for pat, repl in _REPLACEMENTS:
        t = re.sub(pat, repl, t, flags=re.I)
    t = _WS.sub(" ", t)
    if len(t) > max_chars:
        t = t[:max_chars].rsplit(" ", 1)[0].strip() or t[:max_chars]
    return t


def fts_query_text(normalized: str) -> str:
    """Plain text for `plainto_tsquery` (lexeme extraction happens in PostgreSQL)."""
    return normalized


def is_smalltalk_query(raw: str) -> bool:
    """
    Detect greeting / chit-chat prompts and bypass retrieval-heavy path.

    These messages are not factual university queries and should return
    a friendly assistant greeting.
    """
    t = _WS.sub(" ", raw.strip().lower())
    t = _NON_ALNUM.sub("", t)
    if not t:
        return False
    return any(p.match(t) for p in _GREETING_PATTERNS)

"""Link resolution and classification (no HTTP)."""

from __future__ import annotations

from urllib.parse import urlparse

from app.crawler.normalization import looks_like_pdf_url, normalize_url, resolve_url
from app.crawler.types import LinkKind, ParsedLink


def classify_url(canonical_url: str) -> LinkKind:
    """Classify a normalized absolute URL."""
    if looks_like_pdf_url(canonical_url):
        return "pdf"
    p = urlparse(canonical_url)
    if p.scheme in ("http", "https"):
        return "html"
    return "other"


def parse_links_from_href(href: str, base_url: str) -> ParsedLink | None:
    """
    Resolve `href` against page `base_url`, normalize, and classify.

    Returns None for unparseable URLs, non-http(s) schemes, or fragment-only junk.
    """
    href = href.strip()
    if not href or href.startswith("#"):
        return None
    try:
        resolved = resolve_url(href, base_url)
        canonical = normalize_url(resolved)
    except ValueError:
        return None
    kind = classify_url(canonical)
    if kind == "other":
        return None
    return ParsedLink(raw_href=href, absolute_url=canonical, kind=kind)


def content_type_is_pdf(content_type: str | None) -> bool:
    if not content_type:
        return False
    return "application/pdf" in content_type.split(";")[0].strip().lower()

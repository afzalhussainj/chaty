"""URL canonicalization for deduplication and safe comparison."""

from __future__ import annotations

import posixpath
from urllib.parse import parse_qsl, quote, unquote, urlencode, urljoin, urlparse, urlunparse


def resolve_url(href: str, base: str) -> str:
    """Resolve a possibly relative `href` against `base` (no other normalization)."""
    joined = urljoin(base, href.strip())
    return joined


def normalize_url(url: str, base: str | None = None) -> str:
    """
    Return a stable canonical URL string for deduplication and loop detection.

    - Lowercases scheme and host (punycode for IDN hosts).
    - Drops default ports (:80 / :443).
    - Strips fragments.
    - Sorts query parameters lexicographically (stable encoding).
    - Normalizes path with posix semantics (``..``, ``.``) and removes trailing slash
      except the root path ``/``.
    """
    if base:
        url = resolve_url(url, base)
    else:
        url = url.strip()
    parsed = urlparse(url)
    if not parsed.netloc:
        msg = "URL must include a host"
        raise ValueError(msg)

    scheme = (parsed.scheme or "http").lower()
    if scheme not in ("http", "https"):
        msg = f"Unsupported URL scheme: {scheme!r}"
        raise ValueError(msg)

    hostname = parsed.hostname
    if hostname is None:
        msg = "URL missing hostname"
        raise ValueError(msg)
    try:
        host_ascii = hostname.encode("idna").decode("ascii")
    except UnicodeError as e:
        msg = "Invalid internationalized domain name"
        raise ValueError(msg) from e
    host_lower = host_ascii.lower()

    port = parsed.port
    if port is None or (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
        netloc = host_lower
    else:
        netloc = f"{host_lower}:{port}"

    path = _normalize_path(parsed.path or "")

    pairs = parse_qsl(parsed.query, keep_blank_values=True)
    pairs.sort()
    query = urlencode(pairs, doseq=True)

    return urlunparse((scheme, netloc, path, "", query, ""))


def _normalize_path(raw_path: str) -> str:
    decoded = unquote(raw_path)
    if decoded in ("", "/"):
        return "/"
    collapsed = posixpath.normpath(decoded)
    if not collapsed.startswith("/"):
        collapsed = "/" + collapsed
    if collapsed != "/" and collapsed.endswith("/"):
        collapsed = collapsed.rstrip("/")
    return quote(collapsed, safe="/")


def looks_like_pdf_url(url: str) -> bool:
    """
    Heuristic PDF detection from URL alone (before fetch).

    Case-insensitive ``.pdf`` suffix on the last path segment (query ignored).
    """
    p = urlparse(url)
    path = unquote(p.path or "")
    segment = path.rsplit("/", 1)[-1]
    return bool(segment) and segment.lower().endswith(".pdf")

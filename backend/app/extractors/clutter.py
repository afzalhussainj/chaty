"""Deterministic removal of common non-main chrome before core extraction."""

from __future__ import annotations

from bs4 import BeautifulSoup

# Fixed order for reproducibility across runs.
_TAG_SELECTORS = (
    "header",
    "footer",
    "nav",
    "aside",
    "[role=banner]",
    "[role=navigation]",
    "[role=complementary]",
    "[role=contentinfo]",
)

_CLASS_SUBSTRINGS = (
    "cookie",
    "consent",
    "banner",
    "navbar",
    "nav-bar",
    "site-header",
    "site-footer",
    "sidebar",
    "side-bar",
    "skip-link",
    "breadcrumb",
)


def strip_clutter_html(html: str, _source_url: str) -> str:
    """
    Remove structural chrome and obvious cookie/banner blocks.

    Runs before trafilatura/readability; keeps main extraction separate from crawling.
    """
    soup = BeautifulSoup(html, "html.parser")
    for sel in _TAG_SELECTORS:
        for node in soup.select(sel):
            node.decompose()
    for node in soup.find_all(True):
        if not node.attrs:
            continue
        class_list = node.get("class")
        ident = node.get("id")
        blob = " ".join(
            [
                *(class_list or []),
                str(ident or ""),
            ]
        ).lower()
        if any(s in blob for s in _CLASS_SUBSTRINGS):
            node.decompose()
    return str(soup)

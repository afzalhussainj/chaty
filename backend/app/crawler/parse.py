"""HTML parsing (links + title); keep free of DB or policy."""

from __future__ import annotations

from bs4 import BeautifulSoup


def extract_title(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    if soup.title and soup.title.string:
        return soup.title.string.strip() or None
    og = soup.find("meta", property="og:title")
    if og and og.get("content"):
        return str(og["content"]).strip() or None
    return None


def extract_anchor_hrefs(html: str) -> list[str]:
    """Return raw `href` attribute values from `<a>` tags (may be relative)."""
    soup = BeautifulSoup(html, "html.parser")
    out: list[str] = []
    for tag in soup.find_all("a", href=True):
        href = tag.get("href")
        if isinstance(href, str) and href:
            out.append(href)
    return out

"""Optional sitemap.xml discovery (best-effort, namespace-tolerant)."""

from __future__ import annotations

import re
from xml.etree import ElementTree as ET

from app.crawler.fetch import HttpFetcher
from app.crawler.normalization import normalize_url

LOC_RE = re.compile(r"<loc[^>]*>\s*([^<]+)\s*</loc>", re.IGNORECASE)

_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def fetch_sitemap_urls(
    base_url: str,
    fetcher: HttpFetcher,
    *,
    paths: tuple[str, ...] = ("/sitemap.xml", "/sitemap_index.xml"),
) -> list[str]:
    """
    Try common sitemap paths relative to the site origin and return normalized URLs.

    Follows one level of sitemap index files (nested sitemap locs).
    """
    from urllib.parse import urljoin, urlparse

    p = urlparse(base_url)
    origin = f"{p.scheme}://{p.netloc}"
    out: list[str] = []
    for path in paths:
        sm_url = urljoin(origin + "/", path.lstrip("/"))
        try:
            fr = fetcher.fetch(sm_url)
        except OSError:
            continue
        if fr.status_code >= 400 or not fr.body:
            continue
        text = fr.body.decode("utf-8", errors="replace")
        urls = _parse_sitemap_body(text)
        for u in urls:
            try:
                out.append(normalize_url(u))
            except ValueError:
                continue
    return list(dict.fromkeys(out))


def _parse_sitemap_body(xml_text: str) -> list[str]:
    urls: list[str] = []
    # Regex fallback (works when namespaces break ElementTree)
    urls.extend(LOC_RE.findall(xml_text))
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return urls
    # Try default namespace
    for loc in root.findall(".//sm:loc", _NS):
        if loc.text:
            urls.append(loc.text.strip())
    for loc in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
        if loc.text:
            urls.append(loc.text.strip())
    # plain tag names (no namespace)
    for loc in root.findall(".//loc"):
        if loc.text:
            urls.append(loc.text.strip())
    return list(dict.fromkeys(urls))

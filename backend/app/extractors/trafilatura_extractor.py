"""Trafilatura-backed main content extraction (deterministic options)."""

from __future__ import annotations

import trafilatura

from app.extractors.markdown_headings import headings_from_markdown
from app.extractors.protocol import HeadingNode, HtmlExtractionResult

TRAFILATURA_VERSION = getattr(trafilatura, "__version__", "unknown")


class TrafilaturaHtmlExtractor:
    """Default extractor: boilerplate removal + Markdown output + metadata."""

    @property
    def id(self) -> str:
        return "trafilatura"

    def extract(self, html: str, *, source_url: str) -> HtmlExtractionResult:
        md = trafilatura.extract(
            html,
            url=source_url,
            output_format="markdown",
            favor_precision=True,
            favor_recall=False,
            include_comments=False,
            include_tables=True,
            include_images=False,
            include_links=False,
        )
        text = (md or "").strip()
        fmt = "markdown"
        if not text:
            plain = trafilatura.extract(
                html,
                url=source_url,
                output_format="txt",
                favor_precision=True,
                favor_recall=False,
                include_comments=False,
                include_tables=True,
                include_images=False,
                include_links=False,
            )
            text = (plain or "").strip()
            fmt = "plain"
        meta = trafilatura.extract_metadata(html)
        title = str(meta.title).strip() if meta and meta.title else None
        language = None
        if meta and meta.language:
            language = str(meta.language)[:32]

        headings: tuple[HeadingNode, ...]
        if text:
            headings = headings_from_markdown(text)
        else:
            headings = ()

        return HtmlExtractionResult(
            text=text,
            format=fmt,
            title=title,
            language=language,
            headings=headings,
            extractor_id=self.id,
            extractor_version=str(TRAFILATURA_VERSION),
        )

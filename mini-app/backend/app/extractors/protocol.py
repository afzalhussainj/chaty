"""Swappable HTML extraction interface (no crawling or DB)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class HeadingNode:
    """Single heading in reading order."""

    level: int
    text: str


@dataclass(frozen=True, slots=True)
class HtmlExtractionResult:
    """Deterministic extraction output for one HTML document."""

    text: str
    """Primary body text (Markdown when `format` is markdown)."""

    format: str
    """`markdown` or `plain`."""

    title: str | None
    language: str | None
    headings: tuple[HeadingNode, ...] = ()
    extractor_id: str = "unknown"
    extractor_version: str = "0"


@runtime_checkable
class HtmlExtractor(Protocol):
    """Pluggable extractor; implement for trafilatura, readability, cloud APIs, etc."""

    @property
    def id(self) -> str:
        """Stable identifier for provenance in stored metadata."""

    def extract(self, html: str, *, source_url: str) -> HtmlExtractionResult:
        """`html` must be decoded text; `source_url` aids relative resolution and hints."""


@dataclass
class ExtractorChain:
    """Compose preprocessors (e.g. clutter removal) before a delegate `HtmlExtractor`."""

    preprocessors: tuple[Callable[[str, str], str], ...]
    extractor: HtmlExtractor

    @property
    def id(self) -> str:
        return self.extractor.id

    def extract(self, html: str, *, source_url: str) -> HtmlExtractionResult:
        text = html
        for fn in self.preprocessors:
            text = fn(text, source_url)
        return self.extractor.extract(text, source_url=source_url)

"""Pluggable HTML extractors (no DB or HTTP orchestration here).

Heavy backends (e.g. trafilatura) are imported from submodules to avoid import-time deps.
"""

from app.extractors.protocol import (
    ExtractorChain,
    HeadingNode,
    HtmlExtractionResult,
    HtmlExtractor,
)

__all__ = [
    "ExtractorChain",
    "HeadingNode",
    "HtmlExtractionResult",
    "HtmlExtractor",
]

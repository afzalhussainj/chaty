"""Parse heading hierarchy from Markdown lines (deterministic)."""

from __future__ import annotations

import re

from app.extractors.protocol import HeadingNode

_ATX_HEADER = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def headings_from_markdown(markdown: str) -> tuple[HeadingNode, ...]:
    """Extract ATX-style headings in document order."""
    out: list[HeadingNode] = []
    for line in markdown.splitlines():
        m = _ATX_HEADER.match(line.strip())
        if not m:
            continue
        level = len(m.group(1))
        text = m.group(2).strip()
        if text:
            out.append(HeadingNode(level=level, text=text))
    return tuple(out)

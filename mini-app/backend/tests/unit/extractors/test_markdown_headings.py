"""Heading hierarchy from Markdown."""

from __future__ import annotations

from app.extractors.markdown_headings import headings_from_markdown


def test_structured_headings_in_order() -> None:
    md = "# Title\n\nPara.\n\n## Section A\n\n### Sub\n\n## Section B\n"
    h = headings_from_markdown(md)
    assert [x.level for x in h] == [1, 2, 3, 2]
    assert h[0].text == "Title"
    assert h[2].text == "Sub"


def test_ignores_non_atx_lines() -> None:
    md = "not a heading\n# Real\n"
    h = headings_from_markdown(md)
    assert len(h) == 1

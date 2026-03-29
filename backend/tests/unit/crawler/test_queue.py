"""Frontier duplicate suppression."""

from __future__ import annotations

from app.crawler.queue import CrawlFrontier
from app.crawler.types import FrontierItem


def test_enqueue_twice_same_canonical() -> None:
    f = CrawlFrontier()
    a = FrontierItem("https://example.com/a", 0, None)
    assert f.enqueue(a) is True
    assert f.enqueue(FrontierItem("https://example.com/a", 1, 5)) is False

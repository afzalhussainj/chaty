"""Frontier queue + duplicate detection for BFS crawling."""

from __future__ import annotations

from collections import deque

from app.crawler.types import FrontierItem


class CrawlFrontier:
    """Enqueue/dequeue with a canonical-URL seen set to avoid loops and duplicates."""

    def __init__(self) -> None:
        self._q: deque[FrontierItem] = deque()
        self._seen: set[str] = set()

    def enqueue(self, item: FrontierItem) -> bool:
        """
        Add `item` if its canonical URL was not seen before.

        Returns True if the item was newly enqueued.
        """
        if item.canonical_url in self._seen:
            return False
        self._seen.add(item.canonical_url)
        self._q.append(item)
        return True

    def dequeue(self) -> FrontierItem | None:
        if not self._q:
            return None
        return self._q.popleft()

    def __len__(self) -> int:
        return len(self._q)

    def has_seen(self, canonical_url: str) -> bool:
        return canonical_url in self._seen

    def mark_seen(self, canonical_url: str) -> None:
        """Record a URL without queueing (e.g. already processed as PDF registration)."""
        self._seen.add(canonical_url)

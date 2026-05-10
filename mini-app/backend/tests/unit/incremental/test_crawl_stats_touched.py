"""CrawlStats touched_source_ids serialization."""

from __future__ import annotations

from app.crawler.types import CrawlStats, crawl_stats_to_dict


def test_crawl_stats_to_dict_includes_touched_ids() -> None:
    s = CrawlStats()
    s.touched_source_ids.extend([10, 20])
    d = crawl_stats_to_dict(s)
    assert d["touched_source_ids"] == [10, 20]

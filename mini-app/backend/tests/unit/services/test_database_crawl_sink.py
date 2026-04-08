"""DatabaseCrawlSink deduplicates by canonical URL (no database)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.models.source import Source
from app.services.crawl_db_sink import DatabaseCrawlSink


def test_upsert_html_creates_then_updates_same_canonical() -> None:
    session = MagicMock()
    repo = MagicMock()
    row_holder: list[Source | None] = [None]

    def get_by_canonical(_tenant_id: int, _canonical: str) -> Source | None:
        return row_holder[0]

    def add(row: Source) -> None:
        row.id = 99
        row_holder[0] = row

    repo.get_by_canonical.side_effect = get_by_canonical
    repo.add.side_effect = add

    with patch("app.services.crawl_db_sink.SourceRepository", return_value=repo):
        sink = DatabaseCrawlSink(session, tenant_id=1, crawl_config_id=1)
        id1 = sink.upsert_html_page(
            canonical_url="https://a.com/x",
            fetched_url="https://a.com/first",
            title="First",
            parent_source_id=None,
        )
        id2 = sink.upsert_html_page(
            canonical_url="https://a.com/x",
            fetched_url="https://a.com/second",
            title="Second",
            parent_source_id=5,
        )

    assert id1 == id2 == 99
    assert repo.add.call_count == 1
    assert row_holder[0] is not None
    assert row_holder[0].url == "https://a.com/second"
    assert row_holder[0].title == "Second"

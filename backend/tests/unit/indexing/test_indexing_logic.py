"""Skip / hash logic and persistence helpers (no live OpenAI)."""

from __future__ import annotations

import hashlib

from app.indexing.persistence import content_hash_hex, resolve_source_url
from app.models.enums import SourceStatus, SourceType
from app.models.extracted import ExtractedDocument
from app.models.source import Source


def test_content_hash_stable() -> None:
    h = content_hash_hex("hello")
    assert h == hashlib.sha256(b"hello").hexdigest()


def test_resolve_source_url_prefers_fetched_url() -> None:
    doc = ExtractedDocument(
        id=1,
        tenant_id=1,
        source_id=1,
        source_snapshot_id=1,
        extraction_hash="x",
        extraction_metadata={
            "fetched_url": "https://final.example/a",
            "source_url": "https://orig.example/b",
        },
    )
    src = Source(
        id=1,
        tenant_id=1,
        url="https://src.example/c",
        canonical_url="https://src.example/c",
        source_type=SourceType.html_page,
        status=SourceStatus.pending,
    )
    assert resolve_source_url(doc, src) == "https://final.example/a"

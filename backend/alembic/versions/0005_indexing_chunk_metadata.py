"""Indexing: chunk denormalized metadata + extracted_documents index fingerprint.

Revision ID: 0005_indexing_chunk_metadata
Revises: 0004_extracted_document_metadata
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_indexing_chunk_metadata"
down_revision: str | None = "0004_extracted_document_metadata"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "extracted_documents",
        sa.Column("indexed_extraction_hash", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "extracted_documents",
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        op.f("ix_extracted_documents_indexed_extraction_hash"),
        "extracted_documents",
        ["indexed_extraction_hash"],
        unique=False,
    )

    op.add_column("document_chunks", sa.Column("source_url", sa.Text(), nullable=True))
    op.add_column("document_chunks", sa.Column("title", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("document_chunks", "title")
    op.drop_column("document_chunks", "source_url")

    op.drop_index(
        op.f("ix_extracted_documents_indexed_extraction_hash"),
        table_name="extracted_documents",
    )
    op.drop_column("extracted_documents", "indexed_at")
    op.drop_column("extracted_documents", "indexed_extraction_hash")

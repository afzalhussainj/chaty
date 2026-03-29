"""Extracted text (per snapshot) and chunks for retrieval / embeddings."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.job import IndexJob
    from app.models.source import Source, SourceSnapshot
    from app.models.tenant import Tenant


# OpenAI text-embedding-3-small / text-embedding-ada-002 compatible dimension.
EMBEDDING_DIMENSION = 1536


class ExtractedDocument(Base):
    """
    Parsed text for a specific SourceSnapshot (one extraction per snapshot).
    Denormalized tenant_id and source_id for tenant-scoped queries without extra joins.
    """

    __tablename__ = "extracted_documents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("source_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    extraction_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    indexed_extraction_hash: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str | None] = mapped_column(String(32), nullable=True)
    full_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # JSON: headings outline, source_url, extractor id/version (ORM name not `metadata`).
    extraction_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    tenant: Mapped[Tenant] = relationship(back_populates="extracted_documents")
    source: Mapped[Source] = relationship(back_populates="extracted_documents")
    source_snapshot: Mapped[SourceSnapshot] = relationship(back_populates="extracted_documents")
    chunks: Mapped[list[DocumentChunk]] = relationship(
        back_populates="extracted_document",
        order_by="DocumentChunk.chunk_index",
    )
    index_jobs: Mapped[list[IndexJob]] = relationship(back_populates="extracted_document")


class DocumentChunk(Base, TimestampMixin):
    """
    Retrieval unit: text + optional heading + page for citations.
    `embedding` is pgvector; FTS `content_tsv` is added in DB (see migration) as generated column.
    """

    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint(
            "extracted_document_id",
            "chunk_index",
            name="uq_document_chunks_document_chunk_index",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    extracted_document_id: Mapped[int] = mapped_column(
        ForeignKey("extracted_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    heading: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(EMBEDDING_DIMENSION),
        nullable=True,
    )

    tenant: Mapped[Tenant] = relationship(back_populates="document_chunks")
    source: Mapped[Source] = relationship(back_populates="document_chunks")
    extracted_document: Mapped[ExtractedDocument] = relationship(back_populates="chunks")

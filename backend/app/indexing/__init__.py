"""Chunking, embeddings, and persistence for retrieval (pgvector + FTS)."""

from __future__ import annotations

from app.indexing.chunker import ChunkDraft, chunk_extracted_document
from app.indexing.embeddings import OpenAIEmbeddingGenerator
from app.indexing.index_job_service import run_index_job
from app.indexing.indexing_service import (
    IndexOutcome,
    index_extracted_document,
    index_source_latest,
    index_sources,
)

__all__ = [
    "ChunkDraft",
    "OpenAIEmbeddingGenerator",
    "IndexOutcome",
    "chunk_extracted_document",
    "index_extracted_document",
    "index_source_latest",
    "index_sources",
    "run_index_job",
]

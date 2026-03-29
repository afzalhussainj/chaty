"""Core multi-tenant domain: sources, documents, chunks, jobs, chat, admin, audit.

Design notes (see assistant response for full rationale):
- tenant_id denormalized on hot paths (chunks, messages, extracted docs) for isolation queries.
- SourceSnapshot preserves immutable history per crawl/ingest version.
- document_chunks.embedding uses pgvector; content_tsv is generated for PostgreSQL FTS.
- Enums stored as VARCHAR(32) for simpler migrations than native PG enums.
- Admin role/tenant pairing enforced with CHECK constraint.

Revision ID: 0002_core_domain
Revises: 0001_initial
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import INET, JSONB

revision: str = "0002_core_domain"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EMBEDDING_DIM = 1536


def upgrade() -> None:
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))

    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("settings", JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_tenants_slug"), "tenants", ["slug"], unique=False)

    op.create_table(
        "crawl_configs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("max_depth", sa.Integer(), nullable=True),
        sa.Column("respect_robots_txt", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("allowed_hosts", JSONB(), nullable=True),
        sa.Column("path_prefixes", JSONB(), nullable=True),
        sa.Column("exclude_globs", JSONB(), nullable=True),
        sa.Column("extras", JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_crawl_configs_tenant_id"), "crawl_configs", ["tenant_id"], unique=False)

    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(role = 'super_admin' AND tenant_id IS NULL) OR "
            "(role IN ('tenant_admin', 'tenant_viewer') AND tenant_id IS NOT NULL)",
            name="ck_admin_users_role_tenant_consistency",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_admin_users_email"), "admin_users", ["email"], unique=False)
    op.create_index(op.f("ix_admin_users_role"), "admin_users", ["role"], unique=False)
    op.create_index(op.f("ix_admin_users_tenant_id"), "admin_users", ["tenant_id"], unique=False)

    op.create_table(
        "sources",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("crawl_config_id", sa.Integer(), nullable=True),
        sa.Column("discovered_from_source_id", sa.BigInteger(), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("canonical_url", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("last_crawled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_indexed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extras", JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["crawl_config_id"], ["crawl_configs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["discovered_from_source_id"], ["sources.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "canonical_url", name="uq_sources_tenant_canonical_url"),
    )
    op.create_index(
        op.f("ix_sources_content_hash"),
        "sources",
        ["content_hash"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sources_crawl_config_id"),
        "sources",
        ["crawl_config_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sources_discovered_from_source_id"),
        "sources",
        ["discovered_from_source_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sources_source_type"),
        "sources",
        ["source_type"],
        unique=False,
    )
    op.create_index(op.f("ix_sources_status"), "sources", ["status"], unique=False)
    op.create_index(op.f("ix_sources_tenant_id"), "sources", ["tenant_id"], unique=False)

    op.create_table(
        "source_snapshots",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("source_id", sa.BigInteger(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("raw_content_hash", sa.String(length=128), nullable=True),
        sa.Column("byte_length", sa.BigInteger(), nullable=True),
        sa.Column("mime_type", sa.String(length=255), nullable=True),
        sa.Column("storage_uri", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_id", "version", name="uq_source_snapshots_source_version"),
    )
    op.create_index(
        op.f("ix_source_snapshots_raw_content_hash"),
        "source_snapshots",
        ["raw_content_hash"],
        unique=False,
    )
    op.create_index(
        op.f("ix_source_snapshots_source_id"),
        "source_snapshots",
        ["source_id"],
        unique=False,
    )

    op.create_table(
        "extracted_documents",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.BigInteger(), nullable=False),
        sa.Column("source_snapshot_id", sa.BigInteger(), nullable=False),
        sa.Column("extraction_hash", sa.String(length=128), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("language", sa.String(length=32), nullable=True),
        sa.Column("full_text", sa.Text(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_snapshot_id"], ["source_snapshots.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_snapshot_id"),
    )
    op.create_index(
        op.f("ix_extracted_documents_extraction_hash"),
        "extracted_documents",
        ["extraction_hash"],
        unique=False,
    )
    op.create_index(
        op.f("ix_extracted_documents_source_id"),
        "extracted_documents",
        ["source_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_extracted_documents_source_snapshot_id"),
        "extracted_documents",
        ["source_snapshot_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_extracted_documents_tenant_id"),
        "extracted_documents",
        ["tenant_id"],
        unique=False,
    )

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.BigInteger(), nullable=False),
        sa.Column("extracted_document_id", sa.BigInteger(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("heading", sa.Text(), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["extracted_document_id"], ["extracted_documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "extracted_document_id",
            "chunk_index",
            name="uq_document_chunks_document_chunk_index",
        ),
    )
    op.create_index(
        op.f("ix_document_chunks_content_hash"),
        "document_chunks",
        ["content_hash"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_chunks_extracted_document_id"),
        "document_chunks",
        ["extracted_document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_chunks_source_id"),
        "document_chunks",
        ["source_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_chunks_tenant_id"),
        "document_chunks",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_document_chunks_tenant_source",
        "document_chunks",
        ["tenant_id", "source_id"],
        unique=False,
    )

    op.execute(
        sa.text(
            "ALTER TABLE document_chunks ADD COLUMN content_tsv tsvector "
            "GENERATED ALWAYS AS (to_tsvector('simple', coalesce(content, ''))) STORED"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_document_chunks_content_tsv ON document_chunks USING gin (content_tsv)"
        )
    )
    op.create_table(
        "crawl_jobs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("crawl_config_id", sa.Integer(), nullable=True),
        sa.Column("job_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("priority", sa.Integer(), server_default="0", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("stats", JSONB(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["crawl_config_id"], ["crawl_configs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_id"], ["admin_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_crawl_jobs_created_by_id"),
        "crawl_jobs",
        ["created_by_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_crawl_jobs_crawl_config_id"),
        "crawl_jobs",
        ["crawl_config_id"],
        unique=False,
    )
    op.create_index(op.f("ix_crawl_jobs_job_type"), "crawl_jobs", ["job_type"], unique=False)
    op.create_index(op.f("ix_crawl_jobs_status"), "crawl_jobs", ["status"], unique=False)
    op.create_index(op.f("ix_crawl_jobs_tenant_id"), "crawl_jobs", ["tenant_id"], unique=False)

    op.create_table(
        "index_jobs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.BigInteger(), nullable=True),
        sa.Column("extracted_document_id", sa.BigInteger(), nullable=True),
        sa.Column("job_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("stats", JSONB(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["created_by_id"], ["admin_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["extracted_document_id"], ["extracted_documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_index_jobs_created_by_id"),
        "index_jobs",
        ["created_by_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_index_jobs_extracted_document_id"),
        "index_jobs",
        ["extracted_document_id"],
        unique=False,
    )
    op.create_index(op.f("ix_index_jobs_job_type"), "index_jobs", ["job_type"], unique=False)
    op.create_index(op.f("ix_index_jobs_source_id"), "index_jobs", ["source_id"], unique=False)
    op.create_index(op.f("ix_index_jobs_status"), "index_jobs", ["status"], unique=False)
    op.create_index(op.f("ix_index_jobs_tenant_id"), "index_jobs", ["tenant_id"], unique=False)

    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("external_user_id", sa.String(length=255), nullable=True),
        sa.Column("extras", JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_chat_sessions_external_user_id"),
        "chat_sessions",
        ["external_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_chat_sessions_tenant_id"),
        "chat_sessions",
        ["tenant_id"],
        unique=False,
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.BigInteger(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("retrieval_trace", JSONB(), nullable=True),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "sequence", name="uq_chat_messages_session_sequence"),
    )
    op.create_index(op.f("ix_chat_messages_role"), "chat_messages", ["role"], unique=False)
    op.create_index(
        op.f("ix_chat_messages_session_id"),
        "chat_messages",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_chat_messages_tenant_id"),
        "chat_messages",
        ["tenant_id"],
        unique=False,
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("admin_user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("resource_type", sa.String(length=128), nullable=False),
        sa.Column("resource_id", sa.String(length=64), nullable=False),
        sa.Column("details", JSONB(), nullable=True),
        sa.Column("ip_address", INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["admin_user_id"], ["admin_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(
        op.f("ix_audit_logs_admin_user_id"),
        "audit_logs",
        ["admin_user_id"],
        unique=False,
    )
    op.create_index(op.f("ix_audit_logs_created_at"), "audit_logs", ["created_at"], unique=False)
    op.create_index(
        op.f("ix_audit_logs_resource_id"),
        "audit_logs",
        ["resource_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_logs_resource_type"),
        "audit_logs",
        ["resource_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_logs_tenant_id"),
        "audit_logs",
        ["tenant_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("index_jobs")
    op.drop_table("crawl_jobs")
    op.drop_table("document_chunks")
    op.drop_table("extracted_documents")
    op.drop_table("source_snapshots")
    op.drop_table("sources")
    op.drop_table("admin_users")
    op.drop_table("crawl_configs")
    op.drop_table("tenants")
    op.execute(sa.text("DROP EXTENSION IF EXISTS vector"))

"""Knowledge, analysis, and briefing storage.

Revision ID: 0002_content
Revises: 0001_news
"""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0002_content"
down_revision: str | None = "0001_news"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column(
        "hotspot_events",
        sa.Column("subcategories", JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
    )
    op.create_table(
        "hotspot_event_articles",
        sa.Column(
            "event_id", UUID(as_uuid=True), sa.ForeignKey("hotspot_events.id"), primary_key=True
        ),
        sa.Column(
            "article_id", UUID(as_uuid=True), sa.ForeignKey("news_articles.id"), primary_key=True
        ),
        sa.Column("similarity", sa.Float(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "knowledge_documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("external_id", sa.String(100), unique=True, nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("document_type", sa.String(40), nullable=False),
        sa.Column("exam_scope", JSONB(), nullable=False),
        sa.Column("source_url", sa.Text()),
        sa.Column("license_note", sa.Text(), nullable=False),
        sa.Column("effective_from", sa.Date()),
        sa.Column("effective_to", sa.Date()),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("metadata", JSONB(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            UUID(as_uuid=True),
            sa.ForeignKey("knowledge_documents.id"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("tags", JSONB(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column("embedding_model", sa.String(100), nullable=False),
        sa.Column("metadata", JSONB(), nullable=False),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_knowledge_chunks_document_id"),
    )
    op.create_table(
        "hotspot_analyses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "event_id", UUID(as_uuid=True), sa.ForeignKey("hotspot_events.id"), nullable=False
        ),
        sa.Column("analysis_version", sa.Integer(), nullable=False),
        sa.Column("model_provider", sa.String(100), nullable=False),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("exam_relevance", sa.Integer(), nullable=False),
        sa.Column("clear_test_point", sa.Integer(), nullable=False),
        sa.Column("public_affairs", sa.Integer(), nullable=False),
        sa.Column("timeliness", sa.Integer(), nullable=False),
        sa.Column("source_reliability", sa.Integer(), nullable=False),
        sa.Column("trend_linkage", sa.Integer(), nullable=False),
        sa.Column("essay_interview_value", sa.Integer(), nullable=False),
        sa.Column("total_score", sa.Integer(), nullable=False),
        sa.Column("include_in_hotlist", sa.Boolean(), nullable=False),
        sa.Column("include_in_briefing", sa.Boolean(), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("subcategories", JSONB(), nullable=False),
        sa.Column("exam_types", JSONB(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("brief", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("deep_analysis", JSONB(), nullable=False),
        sa.Column("key_points", JSONB(), nullable=False),
        sa.Column("knowledge_refs", JSONB(), nullable=False),
        sa.Column("evidence_refs", JSONB(), nullable=False),
        sa.Column("insufficient_evidence", sa.Boolean(), nullable=False),
        sa.Column("moderation_status", sa.String(20), nullable=False),
        sa.Column("safety_flags", JSONB(), nullable=False),
        sa.Column("prompt_hash", sa.String(64), nullable=False),
        sa.Column("input_hash", sa.String(64), nullable=False),
        sa.Column("raw_response", JSONB(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint(
            "event_id", "analysis_version", "input_hash", name="uq_hotspot_analyses_event_id"
        ),
    )
    op.create_table(
        "briefings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("briefing_date", sa.Date(), nullable=False),
        sa.Column("timezone", sa.String(100), nullable=False),
        sa.Column("locale", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("intro_text", sa.Text(), nullable=False),
        sa.Column("outro_text", sa.Text(), nullable=False),
        sa.Column("estimated_seconds", sa.Integer(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint(
            "briefing_date", "timezone", "locale", "version", name="uq_briefings_briefing_date"
        ),
    )
    op.create_table(
        "briefing_items",
        sa.Column(
            "briefing_id", UUID(as_uuid=True), sa.ForeignKey("briefings.id"), primary_key=True
        ),
        sa.Column("position", sa.Integer(), primary_key=True),
        sa.Column(
            "hotspot_analysis_id",
            UUID(as_uuid=True),
            sa.ForeignKey("hotspot_analyses.id"),
            nullable=False,
        ),
        sa.Column("tts_text", sa.Text(), nullable=False),
        sa.Column("estimated_seconds", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("briefing_items")
    op.drop_table("briefings")
    op.drop_table("hotspot_analyses")
    op.drop_table("knowledge_chunks")
    op.drop_table("knowledge_documents")
    op.drop_table("hotspot_event_articles")
    op.drop_column("hotspot_events", "subcategories")

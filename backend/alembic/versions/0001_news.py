"""Initial news tables.

Revision ID: 0001_news
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0001_news"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "news_sources",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("source_type", sa.String(16), nullable=False),
        sa.Column("feed_url", sa.Text(), unique=True),
        sa.Column("base_url", sa.Text(), nullable=False),
        sa.Column("reliability_score", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("fetch_interval_minutes", sa.Integer(), nullable=False),
        sa.Column("terms_note", sa.Text(), nullable=False),
        sa.Column("last_success_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "news_articles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "source_id", UUID(as_uuid=True), sa.ForeignKey("news_sources.id"), nullable=False
        ),
        sa.Column("canonical_url", sa.Text(), unique=True, nullable=False),
        sa.Column("source_guid", sa.Text()),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column(
            "fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("author", sa.Text()),
        sa.Column("language", sa.String(16)),
        sa.Column("feed_summary", sa.Text()),
        sa.Column("extracted_text", sa.Text()),
        sa.Column("extraction_quality", sa.String(20), nullable=False),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("normalized_title", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("raw_metadata", JSONB(), nullable=False),
        sa.Column("processing_version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("source_id", "source_guid", name="uq_news_articles_source_guid"),
    )
    op.create_index("ix_news_articles_content_hash", "news_articles", ["content_hash"])
    op.create_table(
        "hotspot_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_title", sa.Text(), nullable=False),
        sa.Column("category", sa.String(100)),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column(
            "representative_article_id", UUID(as_uuid=True), sa.ForeignKey("news_articles.id")
        ),
        sa.Column("cluster_version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "job_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("job_name", sa.String(100), nullable=False),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_count", sa.Integer(), nullable=False),
        sa.Column("duplicate_count", sa.Integer(), nullable=False),
        sa.Column("rejected_count", sa.Integer(), nullable=False),
        sa.Column("error_summary", sa.Text()),
    )


def downgrade() -> None:
    op.drop_table("job_runs")
    op.drop_table("hotspot_events")
    op.drop_index("ix_news_articles_content_hash", table_name="news_articles")
    op.drop_table("news_articles")
    op.drop_table("news_sources")

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AuditMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class NewsSource(AuditMixin, Base):
    __tablename__ = "news_sources"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    source_type: Mapped[str] = mapped_column(String(16))
    feed_url: Mapped[str | None] = mapped_column(Text, unique=True)
    base_url: Mapped[str] = mapped_column(Text)
    reliability_score: Mapped[int] = mapped_column(Integer)
    enabled: Mapped[bool] = mapped_column(default=True)
    fetch_interval_minutes: Mapped[int] = mapped_column(Integer, default=30)
    terms_note: Mapped[str] = mapped_column(Text, default="")
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class NewsArticle(AuditMixin, Base):
    __tablename__ = "news_articles"
    __table_args__ = (
        UniqueConstraint("source_id", "source_guid"),
        Index("ix_news_articles_content_hash", "content_hash"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("news_sources.id"))
    canonical_url: Mapped[str] = mapped_column(Text, unique=True)
    source_guid: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    author: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(String(16))
    feed_summary: Mapped[str | None] = mapped_column(Text)
    extracted_text: Mapped[str | None] = mapped_column(Text)
    extraction_quality: Mapped[str] = mapped_column(String(20), default="feed_only")
    content_hash: Mapped[str | None] = mapped_column(String(64))
    normalized_title: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="new")
    raw_metadata: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    processing_version: Mapped[int] = mapped_column(Integer, default=1)
    source: Mapped[NewsSource] = relationship()


class HotspotEvent(AuditMixin, Base):
    __tablename__ = "hotspot_events"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canonical_title: Mapped[str] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(100))
    subcategories: Mapped[list[str]] = mapped_column(JSONB, default=list)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="new")
    representative_article_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("news_articles.id")
    )
    cluster_version: Mapped[int] = mapped_column(Integer, default=1)


class HotspotEventArticle(Base):
    __tablename__ = "hotspot_event_articles"
    event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("hotspot_events.id"), primary_key=True)
    article_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("news_articles.id"), primary_key=True)
    similarity: Mapped[float] = mapped_column(Float)
    is_primary: Mapped[bool] = mapped_column(default=False)


class JobRun(Base):
    __tablename__ = "job_runs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_name: Mapped[str] = mapped_column(String(100))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="running")
    created_count: Mapped[int] = mapped_column(Integer, default=0)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0)
    rejected_count: Mapped[int] = mapped_column(Integer, default=0)
    error_summary: Mapped[str | None] = mapped_column(Text)

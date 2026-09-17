import uuid
from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.news import AuditMixin


class KnowledgeDocument(AuditMixin, Base):
    __tablename__ = "knowledge_documents"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id: Mapped[str] = mapped_column(String(100), unique=True)
    title: Mapped[str] = mapped_column(Text)
    document_type: Mapped[str] = mapped_column(String(40))
    exam_scope: Mapped[list[str]] = mapped_column(JSONB, default=list)
    source_url: Mapped[str | None] = mapped_column(Text)
    license_note: Mapped[str] = mapped_column(Text)
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)
    content_hash: Mapped[str] = mapped_column(String(64))
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="active")
    metadata_json: Mapped[dict[str, object]] = mapped_column("metadata", JSONB, default=dict)


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (UniqueConstraint("document_id", "chunk_index"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("knowledge_documents.id"))
    chunk_index: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer)
    tags: Mapped[list[str]] = mapped_column(JSONB, default=list)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536))
    embedding_model: Mapped[str] = mapped_column(String(100))
    metadata_json: Mapped[dict[str, object]] = mapped_column("metadata", JSONB, default=dict)


class HotspotAnalysis(Base):
    __tablename__ = "hotspot_analyses"
    __table_args__ = (UniqueConstraint("event_id", "analysis_version", "input_hash"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("hotspot_events.id"))
    analysis_version: Mapped[int] = mapped_column(Integer)
    model_provider: Mapped[str] = mapped_column(String(100))
    model_name: Mapped[str] = mapped_column(String(100))
    exam_relevance: Mapped[int] = mapped_column(Integer)
    clear_test_point: Mapped[int] = mapped_column(Integer)
    public_affairs: Mapped[int] = mapped_column(Integer)
    timeliness: Mapped[int] = mapped_column(Integer)
    source_reliability: Mapped[int] = mapped_column(Integer)
    trend_linkage: Mapped[int] = mapped_column(Integer)
    essay_interview_value: Mapped[int] = mapped_column(Integer)
    total_score: Mapped[int] = mapped_column(Integer)
    include_in_hotlist: Mapped[bool] = mapped_column(default=False)
    include_in_briefing: Mapped[bool] = mapped_column(default=False)
    category: Mapped[str] = mapped_column(String(100))
    subcategories: Mapped[list[str]] = mapped_column(JSONB, default=list)
    exam_types: Mapped[list[str]] = mapped_column(JSONB, default=list)
    reason: Mapped[str] = mapped_column(Text)
    brief: Mapped[str] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text)
    deep_analysis: Mapped[dict[str, object]] = mapped_column(JSONB)
    key_points: Mapped[list[str]] = mapped_column(JSONB, default=list)
    knowledge_refs: Mapped[list[str]] = mapped_column(JSONB, default=list)
    evidence_refs: Mapped[list[str]] = mapped_column(JSONB, default=list)
    insufficient_evidence: Mapped[bool] = mapped_column(default=False)
    moderation_status: Mapped[str] = mapped_column(String(20), default="passed")
    safety_flags: Mapped[list[str]] = mapped_column(JSONB, default=list)
    prompt_hash: Mapped[str] = mapped_column(String(64))
    input_hash: Mapped[str] = mapped_column(String(64))
    raw_response: Mapped[dict[str, object]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Briefing(AuditMixin, Base):
    __tablename__ = "briefings"
    __table_args__ = (UniqueConstraint("briefing_date", "timezone", "locale", "version"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    briefing_date: Mapped[date] = mapped_column(Date)
    timezone: Mapped[str] = mapped_column(String(100))
    locale: Mapped[str] = mapped_column(String(20))
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20))
    intro_text: Mapped[str] = mapped_column(Text)
    outro_text: Mapped[str] = mapped_column(Text)
    estimated_seconds: Mapped[int] = mapped_column(Integer)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class BriefingItem(Base):
    __tablename__ = "briefing_items"
    briefing_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("briefings.id"), primary_key=True)
    hotspot_analysis_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("hotspot_analyses.id"))
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    tts_text: Mapped[str] = mapped_column(Text)
    estimated_seconds: Mapped[int] = mapped_column(Integer)


class UserFeedback(Base):
    __tablename__ = "user_feedback"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True)
    hotspot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("hotspot_events.id"))
    event_type: Mapped[str] = mapped_column(String(20))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    install_id_hash: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.ai.schema import DeepAnalysis


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HealthResponse(ApiModel):
    status: Literal["ok"]
    database: Literal["ok"]


class ErrorDetail(ApiModel):
    code: str
    message: str
    request_id: UUID
    retryable: bool


class ApiError(ApiModel):
    error: ErrorDetail


class HotspotItem(ApiModel):
    id: UUID
    title: str
    summary: str
    category: str
    subcategories: list[str]
    exam_types: list[str]
    importance: Literal["core", "other"]
    published_at: datetime
    source_names: list[str]
    content_version: int


class HotspotList(ApiModel):
    date: date
    items: list[HotspotItem]
    next_cursor: str | None


class SourceLink(ApiModel):
    name: str
    url: str
    published_at: datetime | None


class HotspotDetail(ApiModel):
    id: UUID
    title: str
    category: str
    subcategories: list[str]
    exam_types: list[str]
    importance: Literal["core", "other"]
    brief: str
    summary: str
    deep_analysis: DeepAnalysis
    key_points: list[str]
    knowledge_refs: list[str]
    evidence_refs: list[str]
    insufficient_evidence: bool
    content_version: int
    sources: list[SourceLink]


class BriefingItemResponse(ApiModel):
    position: int
    hotspot_id: UUID
    title: str
    tts_text: str
    estimated_seconds: int


class BriefingResponse(ApiModel):
    id: UUID
    date: date
    timezone: str
    version: int
    generated_at: datetime
    expires_at: datetime
    intro_text: str
    items: list[BriefingItemResponse]
    outro_text: str


class ChatRequest(ApiModel):
    question: str = Field(min_length=1, max_length=500)
    hotspot_id: UUID | None = None
    conversation_id: UUID
    locale: Literal["zh-CN"] = "zh-CN"


class Citation(ApiModel):
    type: Literal["knowledge", "article"]
    id: UUID
    source_url: str | None = None


class ChatResponse(ApiModel):
    answer: str
    citations: list[Citation]
    insufficient_evidence: bool
    provider: Literal["mock", "openai"]
    local_action_suggestion: str | None = None


class FeedbackEvent(ApiModel):
    client_event_id: UUID
    hotspot_id: UUID
    event_type: Literal["click", "read", "collect", "hide"]
    occurred_at: datetime

    @field_validator("occurred_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("occurred_at requires a timezone")
        return value


class FeedbackRequest(ApiModel):
    events: list[FeedbackEvent] = Field(min_length=1, max_length=100)


class FeedbackResponse(ApiModel):
    accepted: int

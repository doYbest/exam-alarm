import base64
import binascii
import uuid
from datetime import UTC, date, datetime, time, timedelta
from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Subquery

from app.api.common import cached_json, fail, require_client_token
from app.db.session import get_session
from app.models.content import Briefing, BriefingItem, HotspotAnalysis
from app.models.news import HotspotEvent, HotspotEventArticle, NewsArticle, NewsSource
from app.schemas.api import ApiError, BriefingResponse, HotspotDetail, HotspotList

router = APIRouter(
    prefix="/v1",
    dependencies=[Depends(require_client_token)],
    responses={401: {"model": ApiError}, 422: {"model": ApiError}},
)


def time_bounds(day: date, timezone: str) -> tuple[datetime, datetime]:
    zone = zone_for(timezone)
    start = datetime.combine(day, time.min, zone).astimezone(UTC)
    end = datetime.combine(day + timedelta(days=1), time.min, zone).astimezone(UTC)
    return start, end


def zone_for(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        fail(422, "INVALID_TIMEZONE", "时区无效")


def encode_cursor(at: datetime, event_id: uuid.UUID) -> str:
    value = f"{at.isoformat()}|{event_id}"
    return base64.urlsafe_b64encode(value.encode("utf-8")).decode("ascii").rstrip("=")


def decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        raw = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
        at_text, event_text = raw.split("|", 1)
        at = datetime.fromisoformat(at_text)
        if at.tzinfo is None:
            raise ValueError("cursor time has no timezone")
        return at, uuid.UUID(event_text)
    except (ValueError, UnicodeDecodeError, binascii.Error):
        fail(422, "INVALID_CURSOR", "分页游标无效")


def latest_analysis_query() -> Subquery:
    rank = func.row_number().over(
        partition_by=HotspotAnalysis.event_id,
        order_by=(HotspotAnalysis.created_at.desc(), HotspotAnalysis.id.desc()),
    )
    return select(HotspotAnalysis.id.label("id"), rank.label("rank")).subquery()


@router.get("/hotspots", response_model=HotspotList)
async def list_hotspots(
    session: Annotated[AsyncSession, Depends(get_session)],
    day: Annotated[date | None, Query(alias="date")] = None,
    timezone: str = "Asia/Shanghai",
    category: str | None = None,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    if_none_match: Annotated[str | None, Header()] = None,
) -> object:
    selected_day = day or datetime.now(zone_for(timezone)).date()
    start, end = time_bounds(selected_day, timezone)
    latest = latest_analysis_query()
    statement = (
        select(HotspotEvent, HotspotAnalysis)
        .join(HotspotAnalysis, HotspotAnalysis.event_id == HotspotEvent.id)
        .join(latest, and_(latest.c.id == HotspotAnalysis.id, latest.c.rank == 1))
        .where(HotspotAnalysis.include_in_hotlist)
        .where(HotspotEvent.last_seen_at >= start, HotspotEvent.last_seen_at < end)
        .order_by(HotspotEvent.last_seen_at.desc(), HotspotEvent.id.desc())
        .limit(limit + 1)
    )
    if category:
        statement = statement.where(HotspotAnalysis.category == category)
    if cursor:
        cursor_at, cursor_id = decode_cursor(cursor)
        statement = statement.where(
            or_(
                HotspotEvent.last_seen_at < cursor_at,
                and_(HotspotEvent.last_seen_at == cursor_at, HotspotEvent.id < cursor_id),
            )
        )
    rows = list((await session.execute(statement)).tuples().all())
    has_more = len(rows) > limit
    rows = rows[:limit]
    event_ids = [event.id for event, _ in rows]
    source_names: dict[uuid.UUID, set[str]] = {event_id: set() for event_id in event_ids}
    if event_ids:
        sources = await session.execute(
            select(HotspotEventArticle.event_id, NewsSource.name)
            .join(NewsArticle, NewsArticle.id == HotspotEventArticle.article_id)
            .join(NewsSource, NewsSource.id == NewsArticle.source_id)
            .where(HotspotEventArticle.event_id.in_(event_ids))
        )
        for event_id, name in sources.tuples():
            source_names[event_id].add(name)
    items = [
        {
            "id": str(event.id),
            "title": event.canonical_title,
            "summary": analysis.summary,
            "category": analysis.category,
            "subcategories": analysis.subcategories,
            "exam_types": analysis.exam_types,
            "importance": "core" if analysis.total_score >= 65 else "other",
            "published_at": event.first_seen_at.isoformat(),
            "source_names": sorted(source_names[event.id]),
            "content_version": analysis.analysis_version,
        }
        for event, analysis in rows
    ]
    next_cursor = encode_cursor(rows[-1][0].last_seen_at, rows[-1][0].id) if has_more else None
    return cached_json(
        {"date": selected_day.isoformat(), "items": items, "next_cursor": next_cursor},
        if_none_match,
    )


@router.get(
    "/hotspots/{hotspot_id}", response_model=HotspotDetail, responses={404: {"model": ApiError}}
)
async def hotspot_detail(
    hotspot_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    if_none_match: Annotated[str | None, Header()] = None,
) -> object:
    event = await session.get(HotspotEvent, hotspot_id)
    if event is None:
        fail(404, "HOTSPOT_NOT_FOUND", "热点不存在")
    analysis = await session.scalar(
        select(HotspotAnalysis)
        .where(HotspotAnalysis.event_id == hotspot_id, HotspotAnalysis.include_in_hotlist)
        .order_by(HotspotAnalysis.created_at.desc(), HotspotAnalysis.id.desc())
        .limit(1)
    )
    if analysis is None:
        fail(404, "HOTSPOT_NOT_FOUND", "热点不存在")
    sources = await session.execute(
        select(NewsArticle, NewsSource.name)
        .join(HotspotEventArticle, HotspotEventArticle.article_id == NewsArticle.id)
        .join(NewsSource, NewsSource.id == NewsArticle.source_id)
        .where(HotspotEventArticle.event_id == hotspot_id)
    )
    payload: dict[str, object] = {
        "id": str(event.id),
        "title": event.canonical_title,
        "category": analysis.category,
        "subcategories": analysis.subcategories,
        "exam_types": analysis.exam_types,
        "importance": "core" if analysis.total_score >= 65 else "other",
        "brief": analysis.brief,
        "summary": analysis.summary,
        "deep_analysis": analysis.deep_analysis,
        "key_points": analysis.key_points,
        "knowledge_refs": analysis.knowledge_refs,
        "evidence_refs": analysis.evidence_refs,
        "insufficient_evidence": analysis.insufficient_evidence,
        "content_version": analysis.analysis_version,
        "sources": [
            {
                "name": name,
                "url": article.canonical_url,
                "published_at": article.published_at.isoformat() if article.published_at else None,
            }
            for article, name in sources.tuples()
        ],
    }
    return cached_json(payload, if_none_match)


@router.get(
    "/briefings/today", response_model=BriefingResponse, responses={404: {"model": ApiError}}
)
async def todays_briefing(
    session: Annotated[AsyncSession, Depends(get_session)],
    day: Annotated[date | None, Query(alias="date")] = None,
    timezone: str = "Asia/Shanghai",
    locale: str = "zh-CN",
    if_none_match: Annotated[str | None, Header()] = None,
) -> object:
    selected_day = day or datetime.now(zone_for(timezone)).date()
    time_bounds(selected_day, timezone)
    briefing = await session.scalar(
        select(Briefing)
        .where(
            Briefing.briefing_date == selected_day,
            Briefing.timezone == timezone,
            Briefing.locale == locale,
            Briefing.status == "ready",
        )
        .order_by(Briefing.version.desc())
        .limit(1)
    )
    if briefing is None:
        fail(404, "BRIEFING_NOT_FOUND", "今日晨报尚未生成", retryable=True)
    rows = await session.execute(
        select(BriefingItem, HotspotAnalysis.event_id, HotspotEvent.canonical_title)
        .join(HotspotAnalysis, HotspotAnalysis.id == BriefingItem.hotspot_analysis_id)
        .join(HotspotEvent, HotspotEvent.id == HotspotAnalysis.event_id)
        .where(BriefingItem.briefing_id == briefing.id)
        .order_by(BriefingItem.position)
    )
    payload: dict[str, object] = {
        "id": str(briefing.id),
        "date": selected_day.isoformat(),
        "timezone": timezone,
        "version": briefing.version,
        "generated_at": briefing.generated_at.isoformat(),
        "expires_at": briefing.expires_at.isoformat(),
        "intro_text": briefing.intro_text,
        "items": [
            {
                "position": item.position,
                "hotspot_id": str(event_id),
                "title": title,
                "tts_text": item.tts_text,
                "estimated_seconds": item.estimated_seconds,
            }
            for item, event_id, title in rows.tuples()
        ],
        "outro_text": briefing.outro_text,
    }
    return cached_json(payload, if_none_match)

import math
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Briefing, BriefingItem, HotspotAnalysis
from app.models.news import HotspotEvent


@dataclass(frozen=True)
class Candidate:
    event_id: uuid.UUID
    analysis_id: uuid.UUID
    category: str
    total_score: int
    eligible: bool
    brief: str


def select_candidates(candidates: list[Candidate], count: int = 3) -> list[Candidate]:
    if not 3 <= count <= 5:
        raise ValueError("briefing count must be 3 to 5")
    selected: list[Candidate] = []
    category_counts: dict[str, int] = {}
    event_ids: set[uuid.UUID] = set()
    for candidate in sorted(candidates, key=lambda item: (-item.total_score, str(item.event_id))):
        if not candidate.eligible or candidate.event_id in event_ids:
            continue
        if category_counts.get(candidate.category, 0) >= 2:
            continue
        selected.append(candidate)
        event_ids.add(candidate.event_id)
        category_counts[candidate.category] = category_counts.get(candidate.category, 0) + 1
        if len(selected) == count:
            break
    return selected if len(selected) >= 3 else []


async def generate_briefing(
    session: AsyncSession,
    day: date,
    timezone: str = "Asia/Shanghai",
    locale: str = "zh-CN",
    count: int = 3,
) -> Briefing | None:
    zone = ZoneInfo(timezone)
    start = datetime.combine(day, time.min, zone).astimezone(UTC)
    end = datetime.combine(day + timedelta(days=1), time.min, zone).astimezone(UTC)
    existing = await session.scalar(
        select(Briefing).where(
            Briefing.briefing_date == day,
            Briefing.timezone == timezone,
            Briefing.locale == locale,
            Briefing.status == "ready",
        )
    )
    if existing:
        return existing
    rows = (
        (
            await session.execute(
                select(HotspotEvent, HotspotAnalysis)
                .join(HotspotAnalysis, HotspotAnalysis.event_id == HotspotEvent.id)
                .where(
                    HotspotEvent.last_seen_at >= start,
                    HotspotEvent.last_seen_at < end,
                )
                .order_by(HotspotAnalysis.created_at.desc())
            )
        )
        .tuples()
        .all()
    )
    latest_by_event: dict[uuid.UUID, Candidate] = {}
    for event, analysis in rows:
        if event.id in latest_by_event:
            continue
        latest_by_event[event.id] = Candidate(
            event_id=event.id,
            analysis_id=analysis.id,
            category=analysis.category,
            total_score=analysis.total_score,
            eligible=analysis.include_in_briefing
            and analysis.moderation_status == "passed"
            and analysis.source_reliability >= 7
            and bool(analysis.evidence_refs)
            and not analysis.insufficient_evidence
            and not analysis.safety_flags,
            brief=analysis.brief,
        )
    selected = select_candidates(list(latest_by_event.values()), count)
    if not selected:
        return None
    generated_at = datetime.now(UTC)
    briefing = Briefing(
        briefing_date=day,
        timezone=timezone,
        locale=locale,
        version=1,
        status="ready",
        intro_text=f"早上好，今天为你筛选了{len(selected)}条值得关注的热点。",
        outro_text="详细内容可以在公考晨报中查看。",
        estimated_seconds=sum(math.ceil(len(item.brief) / 4) for item in selected),
        generated_at=generated_at,
        expires_at=end,
    )
    session.add(briefing)
    await session.flush()
    for position, item in enumerate(selected, start=1):
        session.add(
            BriefingItem(
                briefing_id=briefing.id,
                hotspot_analysis_id=item.analysis_id,
                position=position,
                tts_text=item.brief,
                estimated_seconds=math.ceil(len(item.brief) / 4),
            )
        )
    await session.commit()
    return briefing

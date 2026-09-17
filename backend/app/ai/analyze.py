import hashlib
import json
import uuid

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.schema import ValidatedAnalysis, analysis_input_hash, validate_analysis
from app.core.config import get_settings
from app.core.providers import ai_provider, embedding_provider
from app.models.content import HotspotAnalysis
from app.models.news import HotspotEvent, HotspotEventArticle, NewsArticle, NewsSource
from app.rag.search import search_knowledge

ANALYSIS_VERSION = 1
PROMPT_RULES = (
    "system-rules-v1;hotspot-score-v1;hotspot-content-v1;"
    "仅依据给定新闻和知识块。证据不足时标记 insufficient_evidence。"
    "引用只使用给定 ID。输出符合固定 JSON Schema，禁止额外字段。"
)
PROMPT_HASH = hashlib.sha256(PROMPT_RULES.encode("utf-8")).hexdigest()


def build_prompt(
    articles: list[tuple[NewsArticle, NewsSource]],
    knowledge: list[tuple[str, str]],
) -> str:
    payload = {
        "rules": PROMPT_RULES,
        "articles": [
            {
                "id": str(article.id),
                "title": article.title,
                "published_at": article.published_at.isoformat() if article.published_at else None,
                "source": source.name,
                "source_reliability": source.reliability_score,
                "text": (article.extracted_text or article.feed_summary or "")[:3000],
                "extraction_quality": article.extraction_quality,
            }
            for article, source in articles
        ],
        "knowledge": [{"id": chunk_id, "text": text[:1000]} for chunk_id, text in knowledge],
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


async def analyze_event(session: AsyncSession, event_id: uuid.UUID) -> bool:
    settings = get_settings()
    if settings.ai_provider == "mock":
        raise ValueError("real news analysis is disabled in mock mode")
    event = await session.get(HotspotEvent, event_id)
    if event is None:
        raise ValueError("event not found")
    rows = list(
        (
            await session.execute(
                select(NewsArticle, NewsSource)
                .join(HotspotEventArticle, HotspotEventArticle.article_id == NewsArticle.id)
                .join(NewsSource, NewsSource.id == NewsArticle.source_id)
                .where(HotspotEventArticle.event_id == event_id)
            )
        )
        .tuples()
        .all()
    )
    if not rows:
        raise ValueError("event has no articles")
    query = " ".join(article.title for article, _ in rows)
    retrieved = await search_knowledge(session, query, embedding_provider(), limit=8)
    knowledge = [(str(chunk.id), chunk.text) for chunk, _ in retrieved]
    article_ids = [str(article.id) for article, _ in rows]
    article_hashes = [
        article.content_hash
        or hashlib.sha256((article.title + (article.feed_summary or "")).encode()).hexdigest()
        for article, _ in rows
    ]
    knowledge_ids = [chunk_id for chunk_id, _ in knowledge]
    input_hash = analysis_input_hash(str(event_id), article_ids, article_hashes, knowledge_ids)
    existing = await session.scalar(
        select(HotspotAnalysis.id).where(
            HotspotAnalysis.event_id == event_id,
            HotspotAnalysis.analysis_version == ANALYSIS_VERSION,
            HotspotAnalysis.input_hash == input_hash,
        )
    )
    if existing:
        return False
    prompt = build_prompt(rows, knowledge)
    provider = ai_provider()
    raw_text = await provider.complete(prompt)
    validated: ValidatedAnalysis | None = None
    raw: dict[str, object] = {}
    for attempt in range(2):
        try:
            loaded = json.loads(raw_text)
            if not isinstance(loaded, dict):
                raise TypeError("AI response must be a JSON object")
            raw = loaded
            validated = validate_analysis(
                raw,
                allowed_knowledge_refs=set(knowledge_ids),
                allowed_evidence_refs=set(article_ids),
                source_reliability_cap=min(source.reliability_score for _, source in rows),
            )
            break
        except (TypeError, ValueError, ValidationError) as exc:
            if attempt == 1:
                raise ValueError("AI response failed validation after repair") from exc
            repair_prompt = json.dumps(
                {
                    "original_input": prompt,
                    "invalid_output": raw_text,
                    "validation_error": str(exc),
                },
                ensure_ascii=False,
            )
            raw_text = await provider.complete(repair_prompt)
    assert validated is not None
    result = validated.response
    session.add(
        HotspotAnalysis(
            event_id=event_id,
            analysis_version=ANALYSIS_VERSION,
            model_provider=settings.ai_provider,
            model_name=provider.model_name,
            **result.scores.model_dump(),
            total_score=validated.total_score,
            include_in_hotlist=validated.include_in_hotlist,
            include_in_briefing=validated.include_in_briefing,
            category=result.category,
            subcategories=result.subcategories,
            exam_types=result.exam_types,
            reason=result.reason,
            brief=result.brief,
            summary=result.summary,
            deep_analysis=result.deep_analysis.model_dump(),
            key_points=result.key_points,
            knowledge_refs=result.knowledge_refs,
            evidence_refs=result.evidence_refs,
            insufficient_evidence=result.insufficient_evidence,
            moderation_status="passed",
            safety_flags=result.safety_flags,
            prompt_hash=PROMPT_HASH,
            input_hash=input_hash,
            raw_response=raw,
        )
    )
    event.status = "analyzed"
    await session.commit()
    return True

import hashlib
import json
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.provider import MockAIProvider
from app.ai.schema import analysis_input_hash, validate_analysis
from app.models.content import HotspotAnalysis, KnowledgeChunk, KnowledgeDocument
from app.models.news import HotspotEvent, HotspotEventArticle, NewsArticle, NewsSource

DEMO_SOURCE_URL = "https://example.org/demo"
PROMPT_HASH = hashlib.sha256(b"mock-demo-v1").hexdigest()


async def analyze_demo_event(session: AsyncSession, event_id: uuid.UUID) -> bool:
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
    if not rows or any(source.base_url != DEMO_SOURCE_URL for _, source in rows):
        raise ValueError("mock analysis requires self-authored demo articles")
    document = await session.scalar(
        select(KnowledgeDocument).where(KnowledgeDocument.external_id == "KB-GOV-001")
    )
    if document is None:
        raise ValueError("demo knowledge has not been imported")
    chunks = list(
        (
            await session.scalars(
                select(KnowledgeChunk).where(KnowledgeChunk.document_id == document.id)
            )
        ).all()
    )
    article_ids = [str(article.id) for article, _ in rows]
    knowledge_ids = [str(chunk.id) for chunk in chunks]
    article_hashes = [
        article.content_hash
        or hashlib.sha256((article.title + (article.feed_summary or "")).encode()).hexdigest()
        for article, _ in rows
    ]
    input_hash = analysis_input_hash(str(event_id), article_ids, article_hashes, knowledge_ids)
    existing = await session.scalar(
        select(HotspotAnalysis.id).where(
            HotspotAnalysis.event_id == event_id,
            HotspotAnalysis.analysis_version == 1,
            HotspotAnalysis.input_hash == input_hash,
        )
    )
    if existing:
        return False
    prompt = json.dumps(
        {
            "mode": "self_authored_demo",
            "evidence_refs": article_ids,
            "knowledge_refs": knowledge_ids,
        },
        ensure_ascii=False,
    )
    raw = json.loads(await MockAIProvider().complete(prompt))
    validated = validate_analysis(
        raw,
        allowed_knowledge_refs=set(knowledge_ids),
        allowed_evidence_refs=set(article_ids),
        source_reliability_cap=min(source.reliability_score for _, source in rows),
    )
    result = validated.response
    session.add(
        HotspotAnalysis(
            event_id=event_id,
            analysis_version=1,
            model_provider="mock",
            model_name="self-authored-demo-v1",
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
    await session.commit()
    return True

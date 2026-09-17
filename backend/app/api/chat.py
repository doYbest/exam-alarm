import uuid
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.chat_provider import OpenAIChatProvider
from app.api.common import fail, require_client_token
from app.core.config import get_settings
from app.core.providers import embedding_provider
from app.db.session import get_session
from app.models.content import HotspotAnalysis
from app.models.news import HotspotEvent, NewsArticle
from app.rag.search import search_knowledge
from app.schemas.api import ApiError, ChatRequest, ChatResponse, Citation

router = APIRouter(
    prefix="/v1",
    dependencies=[Depends(require_client_token)],
    responses={401: {"model": ApiError}, 422: {"model": ApiError}},
)


@router.post("/ai/chat", response_model=ChatResponse, responses={404: {"model": ApiError}})
async def chat(
    request: ChatRequest, session: Annotated[AsyncSession, Depends(get_session)]
) -> ChatResponse:
    settings = get_settings()
    analysis = None
    if request.hotspot_id:
        event = await session.get(HotspotEvent, request.hotspot_id)
        if event is None:
            fail(404, "HOTSPOT_NOT_FOUND", "热点不存在")
        analysis = await session.scalar(
            select(HotspotAnalysis)
            .where(
                HotspotAnalysis.event_id == request.hotspot_id,
                HotspotAnalysis.include_in_hotlist,
            )
            .order_by(HotspotAnalysis.created_at.desc())
            .limit(1)
        )
        if analysis is None:
            fail(404, "HOTSPOT_NOT_FOUND", "热点不存在")
        if settings.ai_provider == "mock" and analysis.model_provider == "mock":
            return ChatResponse(
                answer=f"演示模式：{analysis.reason} 以上仅基于自写示例材料。",
                citations=[
                    Citation(type="article", id=uuid.UUID(item), source_url=None)
                    for item in analysis.evidence_refs
                ],
                insufficient_evidence=analysis.insufficient_evidence,
                provider="mock",
            )
    results = await search_knowledge(session, request.question, embedding_provider())
    if settings.ai_provider == "openai":
        if settings.openai_api_key is None or not settings.openai_model:
            fail(503, "CHAT_PROVIDER_NOT_READY", "问答模型尚未配置", retryable=True)
        evidence: dict[str, str] = {}
        citations: dict[str, Citation] = {}
        for chunk, document in results:
            key = f"knowledge:{chunk.id}"
            evidence[key] = f"《{document.title}》：{chunk.text[:1500]}"
            citations[key] = Citation(type="knowledge", id=chunk.id, source_url=document.source_url)
        if analysis is not None and analysis.evidence_refs:
            article_ids = [uuid.UUID(item) for item in analysis.evidence_refs[:8]]
            articles = (
                await session.scalars(select(NewsArticle).where(NewsArticle.id.in_(article_ids)))
            ).all()
            for article in articles:
                key = f"article:{article.id}"
                evidence[key] = (
                    f"{article.title}：{(article.extracted_text or article.feed_summary or '')[:1500]}"
                )
                citations[key] = Citation(
                    type="article", id=article.id, source_url=article.canonical_url
                )
        if not evidence:
            return ChatResponse(
                answer="当前没有足够的知识证据，无法回答这个问题。",
                citations=[],
                insufficient_evidence=True,
                provider="openai",
            )
        provider = OpenAIChatProvider(
            settings.openai_api_key.get_secret_value(), settings.openai_model
        )
        try:
            result = await provider.answer(request.question, evidence)
        except (httpx.HTTPError, ValueError):
            fail(502, "CHAT_PROVIDER_FAILED", "问答服务暂时不可用", retryable=True)
        return ChatResponse(
            answer=result.answer,
            citations=[citations[item] for item in result.citation_ids],
            insufficient_evidence=result.insufficient_evidence,
            provider="openai",
        )
    if not results:
        return ChatResponse(
            answer="当前没有足够的知识证据，无法回答这个问题。",
            citations=[],
            insufficient_evidence=True,
            provider="mock",
        )
    chunk, document = results[0]
    return ChatResponse(
        answer=f"演示模式：检索到自写材料《{document.title}》。{chunk.text[:120]} 这不能替代核对原始资料。",
        citations=[Citation(type="knowledge", id=chunk.id, source_url=document.source_url)],
        insufficient_evidence=True,
        provider="mock",
    )

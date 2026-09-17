from difflib import SequenceMatcher

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.news import HotspotEvent, HotspotEventArticle, NewsArticle


def title_similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right).ratio()


def same_event_candidate(
    left: NewsArticle,
    right: NewsArticle,
    *,
    threshold: float,
    window_hours: int,
) -> float | None:
    left_time = left.published_at or left.fetched_at
    right_time = right.published_at or right.fetched_at
    if abs(left_time - right_time).total_seconds() > window_hours * 3600:
        return None
    similarity = title_similarity(left.normalized_title, right.normalized_title)
    return similarity if similarity >= threshold else None


async def cluster_new_articles(session: AsyncSession) -> int:
    settings = get_settings()
    assigned_article_ids = select(HotspotEventArticle.article_id)
    articles = (
        await session.scalars(
            select(NewsArticle)
            .where(NewsArticle.status == "cleaned")
            .where(NewsArticle.id.not_in(assigned_article_ids))
            .order_by(NewsArticle.published_at, NewsArticle.id)
        )
    ).all()
    if not articles:
        return 0
    events = list((await session.scalars(select(HotspotEvent))).all())
    representatives: dict[object, NewsArticle] = {}
    for event in events:
        if event.representative_article_id:
            article = await session.get(NewsArticle, event.representative_article_id)
            if article:
                representatives[event.id] = article
    for article in articles:
        best_event: HotspotEvent | None = None
        best_similarity = 0.0
        for event in events:
            representative = representatives.get(event.id)
            if representative is None:
                continue
            score = same_event_candidate(
                article,
                representative,
                threshold=settings.event_title_similarity_threshold,
                window_hours=settings.event_window_hours,
            )
            if score is not None and score > best_similarity:
                best_event = event
                best_similarity = score
        timestamp = article.published_at or article.fetched_at
        if best_event is None:
            best_event = HotspotEvent(
                canonical_title=article.title,
                first_seen_at=timestamp,
                last_seen_at=timestamp,
                status="new",
                representative_article_id=article.id,
                subcategories=[],
                cluster_version=settings.cluster_rule_version,
            )
            session.add(best_event)
            await session.flush()
            events.append(best_event)
            representatives[best_event.id] = article
            best_similarity = 1.0
        else:
            best_event.first_seen_at = min(best_event.first_seen_at, timestamp)
            best_event.last_seen_at = max(best_event.last_seen_at, timestamp)
            best_event.status = "new"
        session.add(
            HotspotEventArticle(
                event_id=best_event.id,
                article_id=article.id,
                similarity=best_similarity,
                is_primary=best_event.representative_article_id == article.id,
            )
        )
    await session.commit()
    return len(articles)

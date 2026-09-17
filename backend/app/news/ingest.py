from dataclasses import dataclass
from hashlib import sha256
from urllib.parse import urlsplit

import feedparser
import httpx
import trafilatura
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import NewsArticle, NewsSource
from app.news.normalize import NormalizedArticle, normalize_entry


@dataclass(frozen=True)
class IngestResult:
    created: int
    duplicate: int
    rejected: int


async def save_article(
    session: AsyncSession, source: NewsSource, article: NormalizedArticle
) -> bool:
    checks = [NewsArticle.canonical_url == article.canonical_url]
    if article.source_guid:
        checks.append(
            (NewsArticle.source_id == source.id) & (NewsArticle.source_guid == article.source_guid)
        )
    if article.content_hash:
        checks.append(NewsArticle.content_hash == article.content_hash)
    existing = await session.scalar(select(NewsArticle.id).where(or_(*checks)).limit(1))
    if existing is not None:
        return False
    session.add(
        NewsArticle(
            source_id=source.id,
            canonical_url=article.canonical_url,
            source_guid=article.source_guid,
            title=article.title,
            normalized_title=article.normalized_title,
            published_at=article.published_at,
            feed_summary=article.feed_summary,
            content_hash=article.content_hash,
            status="cleaned",
            raw_metadata={},
        )
    )
    await session.flush()
    return True


async def ingest_feed(session: AsyncSession, source: NewsSource, feed_bytes: bytes) -> IngestResult:
    feed = feedparser.parse(feed_bytes)
    if feed.bozo and not feed.entries:
        raise ValueError(f"invalid feed for source {source.id}")
    created = duplicate = rejected = 0
    for item in feed.entries:
        try:
            normalized = normalize_entry(
                {
                    "id": item.get("id", ""),
                    "link": item.get("link", ""),
                    "title": item.get("title", ""),
                    "summary": item.get("summary", ""),
                    "published": item.get("published", ""),
                }
            )
        except ValueError:
            rejected += 1
            continue
        if await save_article(session, source, normalized):
            created += 1
        else:
            duplicate += 1
    return IngestResult(created=created, duplicate=duplicate, rejected=rejected)


async def fetch_and_ingest(session: AsyncSession, source: NewsSource) -> IngestResult:
    if not source.feed_url or source.source_type not in {"rss", "atom"}:
        raise ValueError("source has no RSS/Atom URL")
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        response = await client.get(source.feed_url)
        response.raise_for_status()
        result = await ingest_feed(session, source, response.content)
        await extract_missing_bodies(session, source, client)
    await session.commit()
    return result


def extract_article_text(html: str) -> str | None:
    text = trafilatura.extract(html, include_comments=False, include_tables=False)
    if not text:
        return None
    normalized = " ".join(text.split())
    return normalized if len(normalized) >= 100 else None


async def extract_missing_bodies(
    session: AsyncSession, source: NewsSource, client: httpx.AsyncClient
) -> None:
    source_host = urlsplit(source.base_url).hostname
    articles = (
        await session.scalars(
            select(NewsArticle)
            .where(
                NewsArticle.source_id == source.id,
                NewsArticle.status == "cleaned",
                NewsArticle.extraction_quality == "feed_only",
            )
            .limit(50)
        )
    ).all()
    for article in articles:
        if urlsplit(article.canonical_url).hostname != source_host:
            article.extraction_quality = "skipped_cross_origin"
            continue
        try:
            response = await client.get(article.canonical_url, follow_redirects=False)
            response.raise_for_status()
            if "text/html" not in response.headers.get("content-type", ""):
                article.extraction_quality = "unsupported_content_type"
                continue
            body = extract_article_text(response.text)
        except (httpx.HTTPError, ValueError):
            article.extraction_quality = "failed"
            continue
        if body is None:
            article.extraction_quality = "feed_only"
            continue
        content_hash = sha256(body.encode("utf-8")).hexdigest()
        duplicate_id = await session.scalar(
            select(NewsArticle.id)
            .where(NewsArticle.content_hash == content_hash, NewsArticle.id != article.id)
            .limit(1)
        )
        article.content_hash = content_hash
        article.extracted_text = body
        article.extraction_quality = "full"
        if duplicate_id is not None:
            article.status = "duplicate"

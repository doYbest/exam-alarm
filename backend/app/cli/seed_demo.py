import asyncio
from pathlib import Path

from sqlalchemy import select

from app.ai.demo import analyze_demo_event
from app.db.session import SessionLocal
from app.knowledge.embedding import MockEmbeddingProvider
from app.knowledge.importer import import_manifest
from app.models.news import HotspotEvent, HotspotEventArticle, NewsArticle, NewsSource
from app.news.cluster import cluster_new_articles
from app.news.ingest import ingest_feed


async def main() -> None:
    async with SessionLocal() as session:
        source = await session.scalar(
            select(NewsSource).where(NewsSource.base_url == "https://example.org/demo")
        )
        if source is None:
            source = NewsSource(
                name="自写示例新闻",
                source_type="manual",
                base_url="https://example.org/demo",
                feed_url=None,
                reliability_score=9,
                enabled=False,
                fetch_interval_minutes=30,
                terms_note="internally-authored-example",
            )
            session.add(source)
            await session.flush()
        else:
            source.reliability_score = 9
        feed = (Path(__file__).resolve().parents[2] / "fixtures/demo-feed.xml").read_bytes()
        result = await ingest_feed(session, source, feed)
        await session.commit()
        print(f"seeded: created={result.created}, duplicate={result.duplicate}")
        knowledge_root = Path(__file__).resolve().parents[3] / "knowledge"
        await import_manifest(
            session,
            knowledge_root / "manifests/kb-gov-001.yaml",
            knowledge_root,
            MockEmbeddingProvider(),
        )
        await cluster_new_articles(session)
        events = (
            await session.scalars(
                select(HotspotEvent)
                .join(HotspotEventArticle, HotspotEventArticle.event_id == HotspotEvent.id)
                .join(NewsArticle, NewsArticle.id == HotspotEventArticle.article_id)
                .where(NewsArticle.source_id == source.id)
                .distinct()
            )
        ).all()
        for event in events:
            await analyze_demo_event(session, event.id)


if __name__ == "__main__":
    asyncio.run(main())

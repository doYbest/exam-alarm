import asyncio
import logging
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, text

from app.ai.analyze import analyze_event
from app.briefing.generate import generate_briefing
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.news import HotspotEvent, JobRun, NewsSource
from app.news.cluster import cluster_new_articles
from app.news.ingest import fetch_and_ingest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
LOCK_ID = 0x45584252494546
CLUSTER_LOCK_ID = 0x4558434C555354
BRIEFING_LOCK_ID = 0x45584252494647
ANALYSIS_LOCK_ID = 0x4558414E414C59


async def collect_feeds() -> None:
    async with SessionLocal() as lock_session:
        acquired = await lock_session.scalar(
            text("SELECT pg_try_advisory_lock(:lock_id)"), {"lock_id": LOCK_ID}
        )
        if not acquired:
            logger.info("feed collection already running")
            return
        async with SessionLocal() as session:
            run = JobRun(job_name="feed_collection", status="running")
            session.add(run)
            await session.commit()
            run_id = run.id
        created = duplicate = rejected = 0
        failures: list[str] = []
        try:
            async with SessionLocal() as session:
                sources = (
                    await session.scalars(
                        select(NewsSource).where(
                            NewsSource.enabled, NewsSource.feed_url.is_not(None)
                        )
                    )
                ).all()
            for source in sources:
                try:
                    async with SessionLocal() as session:
                        result = await fetch_and_ingest(session, source)
                    logger.info(
                        "source=%s created=%d duplicate=%d rejected=%d",
                        source.id,
                        result.created,
                        result.duplicate,
                        result.rejected,
                    )
                    created += result.created
                    duplicate += result.duplicate
                    rejected += result.rejected
                    async with SessionLocal() as session:
                        current_source = await session.get(NewsSource, source.id)
                        if current_source is not None:
                            current_source.last_success_at = datetime.now(UTC)
                            await session.commit()
                except Exception:
                    logger.exception("source collection failed: %s", source.id)
                    failures.append(str(source.id))
        finally:
            async with SessionLocal() as session:
                saved_run = await session.get(JobRun, run_id)
                if saved_run is not None:
                    saved_run.finished_at = datetime.now(UTC)
                    saved_run.status = "partial_failure" if failures else "success"
                    saved_run.created_count = created
                    saved_run.duplicate_count = duplicate
                    saved_run.rejected_count = rejected
                    saved_run.error_summary = ",".join(failures) or None
                    await session.commit()
            await lock_session.execute(
                text("SELECT pg_advisory_unlock(:lock_id)"), {"lock_id": LOCK_ID}
            )


async def cluster_events() -> None:
    async with SessionLocal() as lock_session:
        acquired = await lock_session.scalar(
            text("SELECT pg_try_advisory_lock(:lock_id)"), {"lock_id": CLUSTER_LOCK_ID}
        )
        if not acquired:
            return
        try:
            async with SessionLocal() as session:
                count = await cluster_new_articles(session)
            logger.info("clustered %d articles", count)
        finally:
            await lock_session.execute(
                text("SELECT pg_advisory_unlock(:lock_id)"), {"lock_id": CLUSTER_LOCK_ID}
            )


async def build_daily_briefing() -> None:
    async with SessionLocal() as lock_session:
        acquired = await lock_session.scalar(
            text("SELECT pg_try_advisory_lock(:lock_id)"), {"lock_id": BRIEFING_LOCK_ID}
        )
        if not acquired:
            return
        try:
            day = datetime.now(ZoneInfo("Asia/Shanghai")).date()
            async with SessionLocal() as session:
                briefing = await generate_briefing(session, day)
            logger.info("daily briefing %s", briefing.id if briefing else "no eligible candidates")
        finally:
            await lock_session.execute(
                text("SELECT pg_advisory_unlock(:lock_id)"), {"lock_id": BRIEFING_LOCK_ID}
            )


async def analyze_pending_events() -> None:
    if get_settings().ai_provider == "mock":
        return
    async with SessionLocal() as lock_session:
        acquired = await lock_session.scalar(
            text("SELECT pg_try_advisory_lock(:lock_id)"), {"lock_id": ANALYSIS_LOCK_ID}
        )
        if not acquired:
            return
        try:
            async with SessionLocal() as session:
                ids = list(
                    (
                        await session.scalars(
                            select(HotspotEvent.id).where(HotspotEvent.status == "new").limit(20)
                        )
                    ).all()
                )
            for event_id in ids:
                try:
                    async with SessionLocal() as session:
                        await analyze_event(session, event_id)
                except Exception:
                    logger.exception("analysis failed for event=%s", event_id)
        finally:
            await lock_session.execute(
                text("SELECT pg_advisory_unlock(:lock_id)"), {"lock_id": ANALYSIS_LOCK_ID}
            )


async def main() -> None:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(collect_feeds, "interval", minutes=30, next_run_time=datetime.now(UTC))
    scheduler.add_job(cluster_events, "interval", hours=1)
    scheduler.add_job(analyze_pending_events, "interval", hours=1)
    scheduler.add_job(
        build_daily_briefing,
        "cron",
        hour=5,
        minute=0,
        timezone=ZoneInfo("Asia/Shanghai"),
    )
    scheduler.start()
    logger.info("worker started")
    try:
        await asyncio.Event().wait()
    finally:
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())

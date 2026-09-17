from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.models.news import NewsArticle
from app.news.cluster import same_event_candidate, title_similarity


def article(title: str, at: datetime) -> NewsArticle:
    return NewsArticle(
        id=uuid4(),
        source_id=uuid4(),
        canonical_url=f"https://example.org/{uuid4()}",
        title=title,
        normalized_title=title,
        published_at=at,
        fetched_at=at,
        raw_metadata={},
    )


def test_nearby_titles_cluster_within_window() -> None:
    now = datetime.now(UTC)
    first = article("某地公布基层公共服务流程优化方案", now)
    second = article("某地公布基层公共服务流程优化方案", now + timedelta(hours=1))
    assert same_event_candidate(first, second, threshold=0.82, window_hours=48) == 1.0


def test_old_or_unrelated_articles_do_not_cluster() -> None:
    now = datetime.now(UTC)
    first = article("某地公布基层公共服务流程优化方案", now)
    old = article("某地公布基层公共服务流程优化方案", now - timedelta(days=3))
    unrelated = article("体育赛事结果公布", now)
    assert same_event_candidate(first, old, threshold=0.82, window_hours=48) is None
    assert same_event_candidate(first, unrelated, threshold=0.82, window_hours=48) is None
    assert title_similarity("", "标题") == 0.0

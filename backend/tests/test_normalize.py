from datetime import UTC

import pytest

from app.news.normalize import canonical_url, normalize_entry, parse_published


def test_canonical_url_removes_tracking_but_preserves_identity_query() -> None:
    assert canonical_url("HTTPS://Example.COM/news/?id=7&utm_source=x#part") == (
        "https://example.com/news?id=7"
    )


def test_invalid_url_rejected() -> None:
    with pytest.raises(ValueError):
        canonical_url("file:///etc/passwd")


def test_invalid_or_naive_time_is_not_claimed_as_utc() -> None:
    assert parse_published("2026-09-17 08:00:00") is None
    assert parse_published("not a date") is None


def test_normalize_article() -> None:
    article = normalize_entry(
        {
            "link": "https://example.com/1?utm_source=feed",
            "title": " 基层治理：新举措 ",
            "published": "2026-09-17T08:00:00+08:00",
            "summary": "<p>示例新闻。</p>",
        }
    )
    assert article.normalized_title == "基层治理新举措"
    assert article.published_at is not None
    assert article.published_at.tzinfo == UTC
    assert article.feed_summary == "示例新闻。"

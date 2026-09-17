from pathlib import Path

import feedparser

from app.news.normalize import normalize_entry


def test_fixture_is_valid_and_normalizes() -> None:
    feed = feedparser.parse(Path("fixtures/demo-feed.xml").read_bytes())
    assert not feed.bozo
    assert len(feed.entries) == 1
    article = normalize_entry(dict(feed.entries[0]))
    assert article.canonical_url == "https://example.org/demo/001"
    assert article.published_at is not None

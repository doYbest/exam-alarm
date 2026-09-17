from datetime import UTC, datetime
from uuid import uuid4

from app.ai.analyze import build_prompt
from app.models.news import NewsArticle, NewsSource


def test_prompt_includes_only_bounded_evidence() -> None:
    source = NewsSource(
        id=uuid4(), name="示例", reliability_score=7, base_url="https://example.org"
    )
    article = NewsArticle(
        id=uuid4(),
        source_id=source.id,
        canonical_url="https://example.org/article",
        title="示例标题",
        normalized_title="示例标题",
        published_at=datetime.now(UTC),
        extracted_text="甲" * 4000,
        extraction_quality="full",
        raw_metadata={},
    )
    prompt = build_prompt([(article, source)], [("knowledge-1", "乙" * 2000)])
    assert str(article.id) in prompt
    assert "甲" * 3000 in prompt
    assert "甲" * 3001 not in prompt
    assert "乙" * 1000 in prompt
    assert "乙" * 1001 not in prompt

from app.news.ingest import extract_article_text


def test_extract_requires_substantial_body() -> None:
    short = "<html><body><article><p>太短。</p></article></body></html>"
    long = "<html><body><article><p>" + "公共服务流程优化。" * 30 + "</p></article></body></html>"
    assert extract_article_text(short) is None
    result = extract_article_text(long)
    assert result is not None
    assert "公共服务" in result

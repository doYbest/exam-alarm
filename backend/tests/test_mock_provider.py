import json

import pytest

from app.ai.provider import MockAIProvider
from app.ai.schema import validate_analysis


async def test_mock_provider_only_accepts_demo_and_emits_valid_analysis() -> None:
    provider = MockAIProvider()
    with pytest.raises(ValueError):
        await provider.complete('{"mode":"real_news"}')
    raw = json.loads(
        await provider.complete(
            '{"mode":"self_authored_demo","knowledge_refs":["k"],"evidence_refs":["a"]}'
        )
    )
    validated = validate_analysis(raw, allowed_knowledge_refs={"k"}, allowed_evidence_refs={"a"})
    assert validated.include_in_hotlist

import json

import httpx
import pytest

from app.ai.openai_provider import OpenAIProvider
from app.knowledge.openai_embedding import OpenAIEmbeddingProvider


@pytest.mark.asyncio
async def test_structured_response_request_is_private_and_extracts_text() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["store"] is False
        assert body["text"]["format"]["type"] == "json_schema"
        assert body["text"]["format"]["strict"] is True
        return httpx.Response(
            200,
            json={
                "status": "completed",
                "output": [{"type": "message", "content": [{"type": "output_text", "text": "{}"}]}],
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = OpenAIProvider("test-key", "configured-model", client)
        assert await provider.complete("demo") == "{}"


@pytest.mark.asyncio
async def test_embedding_dimension_is_checked() -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [{"embedding": [0.1]}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = OpenAIEmbeddingProvider("test-key", client=client)
        with pytest.raises(ValueError, match="dimension"):
            await provider.embed("测试")

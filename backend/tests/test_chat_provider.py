import json

import httpx
import pytest

from app.ai.chat_provider import OpenAIChatProvider


@pytest.mark.asyncio
async def test_chat_provider_rejects_unknown_citations() -> None:
    async def respond(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["store"] is False
        return httpx.Response(
            200,
            json={
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": json.dumps(
                                    {
                                        "answer": "未经证实的结论",
                                        "citation_ids": ["article:unknown"],
                                        "insufficient_evidence": False,
                                    }
                                ),
                            }
                        ],
                    }
                ],
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        provider = OpenAIChatProvider("test-key", "test-model", client)
        with pytest.raises(ValueError, match="not supplied"):
            await provider.answer("问题", {"knowledge:known": "证据"})


@pytest.mark.asyncio
async def test_chat_provider_accepts_grounded_answer() -> None:
    def respond(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": json.dumps(
                                    {
                                        "answer": "有证据支持",
                                        "citation_ids": ["knowledge:known"],
                                        "insufficient_evidence": False,
                                    }
                                ),
                            }
                        ],
                    }
                ],
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        result = await OpenAIChatProvider("test-key", "test-model", client).answer(
            "问题", {"knowledge:known": "证据"}
        )
    assert result.answer == "有证据支持"
    assert result.citation_ids == ["knowledge:known"]

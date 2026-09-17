import json

import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.ai.openai_provider import OPENAI_RESPONSES_URL


class ChatCompletion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(min_length=1, max_length=2000)
    citation_ids: list[str] = Field(max_length=8)
    insufficient_evidence: bool


class OpenAIChatProvider:
    def __init__(self, api_key: str, model: str, client: httpx.AsyncClient | None = None) -> None:
        if not api_key or not model:
            raise ValueError("OpenAI API key and model are required")
        self._api_key = api_key
        self._model = model
        self._client = client

    async def answer(self, question: str, evidence: dict[str, str]) -> ChatCompletion:
        payload = {
            "model": self._model,
            "instructions": (
                "只根据输入证据回答中文问题。引用仅使用输入证据的 ID；"
                "证据不足时明确说明并将 insufficient_evidence 设为 true。"
            ),
            "input": json.dumps({"question": question, "evidence": evidence}, ensure_ascii=False),
            "store": False,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "grounded_chat",
                    "strict": True,
                    "schema": ChatCompletion.model_json_schema(),
                }
            },
        }
        if self._client is not None:
            response = await self._client.post(
                OPENAI_RESPONSES_URL,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json=payload,
            )
        else:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    OPENAI_RESPONSES_URL,
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json=payload,
                )
        response.raise_for_status()
        data = response.json()
        if data.get("status") != "completed":
            raise ValueError("AI response did not complete")
        for item in data.get("output", []):
            if item.get("type") != "message":
                continue
            for content in item.get("content", []):
                if content.get("type") == "refusal":
                    raise ValueError("AI provider refused the request")
                if content.get("type") == "output_text":
                    result = ChatCompletion.model_validate_json(content["text"])
                    if not set(result.citation_ids).issubset(evidence):
                        raise ValueError("AI cited evidence that was not supplied")
                    if evidence and not result.insufficient_evidence and not result.citation_ids:
                        raise ValueError("AI answer lacks citations")
                    return result
        raise ValueError("AI response has no output text")

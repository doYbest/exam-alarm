import httpx

from app.ai.schema import AnalysisResponse

OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"


class OpenAIProvider:
    """Server-side structured analysis adapter. The API key never reaches Android."""

    def __init__(self, api_key: str, model: str, client: httpx.AsyncClient | None = None) -> None:
        if not api_key or not model:
            raise ValueError("OpenAI API key and model are required")
        self._api_key = api_key
        self.model_name = model
        self._client = client

    async def complete(self, prompt: str) -> str:
        payload = {
            "model": self.model_name,
            "instructions": "根据输入证据生成公考热点分析；只引用输入中的 ID，不得补造事实。",
            "input": prompt,
            "store": False,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "hotspot_analysis",
                    "strict": True,
                    "schema": AnalysisResponse.model_json_schema(),
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
                if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                    return str(content["text"])
        raise ValueError("AI response has no output text")

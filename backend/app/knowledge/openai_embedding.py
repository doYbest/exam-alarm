import httpx

from app.knowledge.embedding import EMBEDDING_DIMENSION

OPENAI_EMBEDDINGS_URL = "https://api.openai.com/v1/embeddings"


class OpenAIEmbeddingProvider:
    def __init__(
        self,
        api_key: str,
        model_name: str = "text-embedding-3-small",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("OpenAI API key is required")
        if not model_name.startswith("text-embedding-3-"):
            raise ValueError("configured model must support 1536 output dimensions")
        self._api_key = api_key
        self.model_name = model_name
        self._client = client

    async def embed(self, text: str) -> list[float]:
        if not text.strip():
            raise ValueError("embedding input is empty")
        payload = {
            "model": self.model_name,
            "input": text,
            "dimensions": EMBEDDING_DIMENSION,
            "encoding_format": "float",
        }
        if self._client is not None:
            response = await self._client.post(
                OPENAI_EMBEDDINGS_URL,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json=payload,
            )
        else:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    OPENAI_EMBEDDINGS_URL,
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json=payload,
                )
        response.raise_for_status()
        data = response.json()
        values = data["data"][0]["embedding"]
        if not isinstance(values, list) or len(values) != EMBEDDING_DIMENSION:
            raise ValueError("embedding dimension does not match database schema")
        return [float(value) for value in values]

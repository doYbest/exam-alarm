import hashlib
import math
from typing import Protocol

EMBEDDING_DIMENSION = 1536


class EmbeddingProvider(Protocol):
    model_name: str

    async def embed(self, text: str) -> list[float]: ...


class MockEmbeddingProvider:
    """Deterministic lexical vectors for local fixtures and tests only."""

    model_name = "mock-hash-v1"

    async def embed(self, text: str) -> list[float]:
        result = [0.0] * EMBEDDING_DIMENSION
        clean = "".join(text.casefold().split())
        if not clean:
            return result
        tokens = [clean[index : index + 3] for index in range(max(1, len(clean) - 2))]
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % EMBEDDING_DIMENSION
            result[index] += 1.0 if digest[4] % 2 else -1.0
        length = math.sqrt(sum(value * value for value in result))
        return [value / length for value in result] if length else result

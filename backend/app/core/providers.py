from app.ai.openai_provider import OpenAIProvider
from app.ai.provider import AIProvider, MockAIProvider
from app.core.config import get_settings
from app.knowledge.embedding import EmbeddingProvider, MockEmbeddingProvider
from app.knowledge.openai_embedding import OpenAIEmbeddingProvider


def ai_provider() -> AIProvider:
    settings = get_settings()
    if settings.ai_provider == "mock":
        return MockAIProvider()
    if settings.ai_provider == "openai":
        if settings.openai_api_key is None or not settings.openai_model:
            raise ValueError("OPENAI_API_KEY and OPENAI_MODEL are required")
        return OpenAIProvider(settings.openai_api_key.get_secret_value(), settings.openai_model)
    raise ValueError("unknown AI provider")


def embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    if settings.embedding_provider == "mock":
        return MockEmbeddingProvider()
    if settings.embedding_provider == "openai":
        if settings.openai_api_key is None:
            raise ValueError("OPENAI_API_KEY is required")
        return OpenAIEmbeddingProvider(
            settings.openai_api_key.get_secret_value(), settings.openai_embedding_model
        )
    raise ValueError("unknown embedding provider")

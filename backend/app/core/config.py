from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://exambrief:exambrief@localhost:5432/exambrief"
    client_token: str = "local-debug-token-change-me"
    ai_provider: str = "mock"
    embedding_provider: str = "mock"
    log_level: str = "INFO"
    event_title_similarity_threshold: float = Field(default=0.82, ge=0, le=1)
    event_window_hours: int = Field(default=48, ge=1, le=168)
    cluster_rule_version: int = Field(default=1, ge=1)
    openai_api_key: SecretStr | None = None
    openai_model: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"


@lru_cache
def get_settings() -> Settings:
    return Settings()

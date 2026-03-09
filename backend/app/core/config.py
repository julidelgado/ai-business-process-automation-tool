from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ai-business-process-automation"
    app_env: str = "development"
    app_port: int = 8000
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"

    database_url: str = "sqlite:///./automation.db"
    redis_url: str = "redis://localhost:6379/0"

    api_key: str = "dev-api-key"
    secret_key: str = "change-me-please"
    cors_origins: str = "http://localhost:5173"

    ai_provider: str = "fallback"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"

    worker_poll_interval_seconds: float = 2.0
    worker_batch_size: int = 25
    default_retry_attempts: int = 3
    default_retry_backoff_seconds: int = 10

    smtp_dry_run: bool = True
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str = "noreply@example.local"

    request_timeout_seconds: int = Field(default=20, ge=2, le=120)

    webhook_secret: str | None = None

    default_page_size: int = Field(default=50, ge=1, le=200)
    max_page_size: int = Field(default=200, ge=1, le=1000)

    @property
    def cors_origins_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

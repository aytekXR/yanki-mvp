"""Application settings, loaded from environment variables (12-factor style).

Every value has a safe default so the app boots with zero configuration. The most
important default is ``dry_run=True``: out of the box the pipeline runs on the
deterministic mock provider and spends $0.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+psycopg://yanki:yanki@localhost:5432/yanki"

    # Provider credentials (blank in DRY_RUN)
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Pipeline behaviour
    dry_run: bool = True
    prompt_count: int = 10
    panel_engines: str = "anthropic,openai,gemini,perplexity"
    max_responses_per_job: int = 60

    # Worker / queue
    worker_poll_seconds: int = 2
    stale_claim_seconds: int = 300

    # Rate limiting (P5.0) — the LIVE POST /api/v1/analyses is public with real
    # keys; these guard it before any row is created or money is spent.
    analyses_rate_limit_per_ip_hour: int = 5
    analyses_daily_cap: int = 100
    ip_hash_salt: str = ""


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (read once per process)."""
    return Settings()

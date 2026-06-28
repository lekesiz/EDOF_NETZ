from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "EDOF-NETZ"
    debug: bool = False
    secret_key: str = "change-me-in-production"

    database_url: str = "postgresql://edofnetz:edofnetz@localhost:5432/edofnetz"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    wedof_api_key: str | None = None
    wedof_webhook_secret: str | None = None
    pennylane_api_token: str | None = None
    pennylane_default_vat_rate: str = "FR_200"

    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 1 day


@lru_cache
def get_settings() -> Settings:
    return Settings()

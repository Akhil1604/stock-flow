from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "stockflow-api"
    environment: str = "local"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./stockflow.db"
    redis_url: str = "redis://localhost:6379/0"
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "stockflow.events"
    outbox_enabled: bool = True
    admin_api_key: str = "local-admin-key"
    reservation_ttl_minutes: int = 15
    rate_limit_per_minute: int = 120

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

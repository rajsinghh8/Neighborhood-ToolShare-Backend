"""Externalised application configuration (environment variables only)."""
from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Immutable settings snapshot, built once at startup and injected."""

    host: str = "0.0.0.0"
    port: int = 8000
    database_url: str = "mysql+aiomysql://eventforge:eventforge@localhost:3306/eventforge"
    jwt_secret: str = "change-me-in-env"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    default_page_size: int = 20
    max_page_size: int = 100
    kafka_enabled: bool = False
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_audit_topic: str = "eventforge.audit"
    kafka_notification_topic: str = "eventforge.notifications"
    kafka_consumer_group: str = "eventforge-app"
    scheduler_interval_ms: int = 60000
    scheduler_enabled: bool = True
    seed_demo_data: bool = False
    db_connect_retries: int = 30
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Settings":
        defaults = cls()
        return cls(
            host=os.environ.get("APP_HOST", defaults.host),
            port=int(os.environ.get("APP_PORT", defaults.port)),
            database_url=os.environ.get("DATABASE_URL", defaults.database_url),
            jwt_secret=os.environ.get("JWT_SECRET", defaults.jwt_secret),
            jwt_expire_minutes=int(os.environ.get("JWT_EXPIRE_MINUTES", defaults.jwt_expire_minutes)),
            default_page_size=int(os.environ.get("DEFAULT_PAGE_SIZE", defaults.default_page_size)),
            max_page_size=int(os.environ.get("MAX_PAGE_SIZE", defaults.max_page_size)),
            kafka_enabled=_env_bool("KAFKA_ENABLED", defaults.kafka_enabled),
            kafka_bootstrap_servers=os.environ.get("KAFKA_BOOTSTRAP_SERVERS", defaults.kafka_bootstrap_servers),
            kafka_audit_topic=os.environ.get("KAFKA_AUDIT_TOPIC", defaults.kafka_audit_topic),
            kafka_notification_topic=os.environ.get("KAFKA_NOTIFICATION_TOPIC", defaults.kafka_notification_topic),
            kafka_consumer_group=os.environ.get("KAFKA_CONSUMER_GROUP", defaults.kafka_consumer_group),
            scheduler_interval_ms=int(os.environ.get("SCHEDULER_INTERVAL_MS", defaults.scheduler_interval_ms)),
            scheduler_enabled=_env_bool("SCHEDULER_ENABLED", defaults.scheduler_enabled),
            seed_demo_data=_env_bool("SEED_DEMO_DATA", defaults.seed_demo_data),
            db_connect_retries=int(os.environ.get("DB_CONNECT_RETRIES", defaults.db_connect_retries)),
            log_level=os.environ.get("LOG_LEVEL", defaults.log_level),
        )

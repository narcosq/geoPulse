"""Module for load settings form `.env` or if server running with parameter
`dev` from `.env.dev`"""
import os
import pathlib
from functools import lru_cache
from typing import Optional

from dotenv import find_dotenv
from pydantic import Extra
from pydantic.types import StrictStr

from pydantic_settings import BaseSettings

__all__ = ["Settings", "get_settings"]


class _Settings(BaseSettings):
    class Config:
        """Configuration of settings."""

        #: str: env file encoding.
        env_file_encoding = "utf-8"
        # #: str: allow custom fields in model.
        arbitrary_types_allowed = True
        #: bool: case sensitive for fields.
        case_sensitive = True
        #: str: delimiter for nested fields.
        env_nested_delimiter = "__"
        #: str: env file.
        extra = Extra.ignore


class Logger(_Settings):
    """Logger settings."""

    #: str: Level of logging which outs in std
    LEVEL: StrictStr = "INFO"
    #: pathlib.Path: Path of saving logs on local storage.
    CONFIG_FILE: pathlib.Path = pathlib.Path("config/logging.json")


class Postgres(_Settings):
    """Postgresql settings."""

    #: str: Postgresql database dsn.
    DSN: str


class Redis(_Settings):
    """Redis settings."""

    #: str: Redis dsn.
    DSN: str


class CircuitBreaker(_Settings):
    """Circuit breaker defaults."""

    MAX_FAILURES: int = 5
    RESET_TIMEOUT_SECONDS: float = 30.0


class Kafka(_Settings):
    """Kafka settings."""

    #: str: Kafka bootstrap servers.
    BOOTSTRAP_SERVERS: str = "localhost:9092"
    #: str: Kafka consumer group ID.
    CONSUMER_GROUP_ID: str = "geopulse-consumer"
    #: str: Kafka topics prefix.
    TOPICS_PREFIX: str = "geopulse"


class Firebase(_Settings):
    """Firebase settings."""

    #: str: Path to Firebase credentials JSON file.
    CREDENTIALS_PATH: Optional[str] = None
    #: str: Firebase project ID.
    PROJECT_ID: Optional[str] = None
    #: dict: Firebase credentials (can be passed as JSON string in env).
    CREDENTIALS: Optional[str] = None


class GoogleMaps(_Settings):
    """Google Maps API settings."""

    #: str: Google Maps API key.
    API_KEY: Optional[str] = None
    #: str: Google Maps API base URL.
    BASE_URL: str = "https://maps.googleapis.com/maps/api"


class Telegram(_Settings):
    """Telegram Bot API settings."""

    #: str: Telegram bot token.
    BOT_TOKEN: Optional[str] = None
    #: str: Telegram API base URL.
    BASE_URL: str = "https://api.telegram.org/bot"


class Celery(_Settings):
    """Celery settings."""

    #: str: Celery broker URL (Redis).
    BROKER_URL: str = "redis://localhost:6379/0"
    #: str: Celery result backend URL (Redis).
    RESULT_BACKEND: str = "redis://localhost:6379/0"
    #: str: Celery task serializer.
    TASK_SERIALIZER: str = "json"
    #: str: Celery result serializer.
    RESULT_SERIALIZER: str = "json"
    #: bool: Accept content.
    ACCEPT_CONTENT: list = ["json"]
    #: str: Timezone.
    TIMEZONE: str = "UTC"
    #: bool: Enable UTC.
    ENABLE_UTC: bool = True


class Settings(_Settings):
    """Server settings.

    Formed from `.env` or `.env.dev`.
    """

    #: str: Name of API service.
    API_INSTANCE_APP_NAME: str = "geo-pulse-service"
    #: str: API version.
    API_INSTANCE_VERSION: str = "v1.0.0"
    #: str: API instance stage.
    API_INSTANCE_STAGE: str = "development"
    #: str: Sentry instance dsn.
    SENTRY_DSN: Optional[str] = None

    #: str: Open telemetry protocol endpoint.
    OTLP_ENDPOINT: Optional[str] = None

    #: Postgres: Postgresql settings.
    POSTGRES: Postgres

    #: Redis: Redis settings.
    REDIS: Redis

    #: Logger: Logger settings.
    LOGGER: Logger = Logger()

    #: CircuitBreaker: Circuit breaker defaults.
    CIRCUIT_BREAKER: CircuitBreaker = CircuitBreaker()

    #: Kafka: Kafka settings.
    KAFKA: Kafka = Kafka()

    #: Firebase: Firebase settings.
    FIREBASE: Firebase = Firebase()

    #: GoogleMaps: Google Maps API settings.
    GOOGLE_MAPS: GoogleMaps = GoogleMaps()

    #: Telegram: Telegram Bot API settings.
    TELEGRAM: Telegram = Telegram()

    #: Celery: Celery settings.
    CELERY: Celery = Celery()



@lru_cache()
def get_settings(env_file: str = ".env", secrets_dir: str = "/run/secrets") -> Settings:
    """Create settings instance."""
    return Settings(_env_file=find_dotenv(env_file), _secrets_dir=secrets_dir)

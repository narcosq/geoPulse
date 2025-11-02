"""All connectors in declarative container."""

from dependency_injector import containers, providers

from .redis import Redis
from .postgresql import Postgresql
from .sqlalchemy import SQLAlchemyConnector

from app.pkg.settings import Settings, settings

__all__ = [
    "Connectors",
    "Postgresql",
    "Redis",
]


class Connectors(containers.DeclarativeContainer):
    """Declarative container with connectors."""

    configuration: Settings = providers.Configuration(
        name="settings",
        pydantic_settings=[settings],
    )

    # Create postgresql connector.
    postgresql = providers.Factory(
        Postgresql,
        dsn=configuration.POSTGRES.DSN,
    )

    # Create redis connector.
    redis = providers.Factory(
        Redis,
        dsn=configuration.REDIS.DSN,
    )

    # SQLAlchemy async engine/session
    sqlalchemy = providers.Singleton(
        SQLAlchemyConnector,
        dsn=configuration.POSTGRES.DSN,
    )

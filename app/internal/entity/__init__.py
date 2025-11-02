from dependency_injector import containers, providers

from app.internal.repository import postgresql


class Entities(containers.DeclarativeContainer):

    repositories: postgresql.Repositories = providers.Container(
        postgresql.Repositories,  # type: ignore
    )

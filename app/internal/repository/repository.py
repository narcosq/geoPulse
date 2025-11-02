from abc import ABC
from typing import List, TypeVar, Optional


from app.pkg.connectors.sqlalchemy import SQLAlchemyConnector
from app.pkg.connectors.base_connector import BaseConnector
from app.pkg.models.base import Model

__all__ = ["Repository", "BaseRepository"]


BaseRepository = TypeVar("BaseRepository", bound="Repository")


class Repository(ABC):
    """Base repository interface."""
    postgresql: Optional[BaseConnector] = None
    _sqlalchemy: Optional[SQLAlchemyConnector] = None

    def __init__(
        self,
        postgresql: Optional[BaseConnector] = None,
        sqlalchemy: Optional[SQLAlchemyConnector] = None,
    ):
        self.postgresql = postgresql
        self._sqlalchemy = sqlalchemy

    async def create(self, cmd: Model) -> Model:
        raise NotImplementedError

    async def read(self, query: Model) -> Model:
        raise NotImplementedError

    async def read_all(self) -> List[Model]:
        raise NotImplementedError

    async def update(self, cmd: Model) -> Model:
        raise NotImplementedError

    async def delete(self, cmd: Model) -> Model:
        raise NotImplementedError

    @property
    def connection_kwargs(self):
        kwargs = {}
        if self.postgresql is not None:
            kwargs.update(postgresql=self.postgresql)
        return kwargs

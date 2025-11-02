"""Postgresql connector."""
import typing
import urllib.parse
from contextlib import asynccontextmanager

import aiopg
import pydantic
from aiopg import Connection

from .base_connector import BaseConnector

__all__ = ["Postgresql"]


class Postgresql(BaseConnector):
    dsn: str

    def __init__(
        self,
        dsn: str,
    ):
        """Settings for create postgresql dsn.

        Args:
            dsn: str
        """
        self.dsn = dsn

    def get_dsn(self) -> str:
        """Description of ``BaseConnector.get_dsn``."""
        return self.dsn

    @asynccontextmanager
    async def get_connect(self) -> typing.AsyncIterator[Connection]:
        """Create pool of connectors to a Postgres database.

        Yields:
            ``aiopg.Connection instance`` in asynchronous context manager.
        """
        async with aiopg.create_pool(self.get_dsn()) as pool:
            async with pool.acquire() as connection:
                yield connection

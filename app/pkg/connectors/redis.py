from contextlib import asynccontextmanager
from typing import AsyncIterator

from redis import asyncio as aioredis

from app.pkg.connectors.base_connector import BaseConnector
from app.pkg.logger import logger

__all__ = ["Redis"]


class Redis(BaseConnector):
    dsn: str

    def __init__(self, dsn: str):
        """Redis connector constructor.

        Args:
            dsn (str): DSN for connection
        """
        self.dsn = dsn

    def get_dsn(self) -> str:
        """Get DSN for connection."""
        return self.dsn

    @asynccontextmanager
    async def get_connect(self) -> AsyncIterator[aioredis.Redis]:
        """Get connection pool in asynchronous context."""
        redis = aioredis.from_url(self.get_dsn())
        try:
            yield redis
        finally:
            await redis.close()

    async def ping(self) -> bool:
        """Check Redis availability.

        Returns:
            bool: True if Redis responds, False otherwise.
        """
        async with self.get_connect() as redis:
            return await redis.ping()

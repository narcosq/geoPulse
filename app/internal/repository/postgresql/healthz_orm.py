"""Health check repository."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.internal.repository.repository import Repository


__all__ = ["HealthzOrmRepository"]


class HealthzOrmRepository(Repository):
    """Repository for verifying infrastructure dependencies (DB, Redis)."""

    async def check_connection(self) -> bool:
        """
        Verify connectivity to the primary database by executing a simple query.
        Returns True if successful, otherwise raises an exception.
        """
        async with self._sqlalchemy.session() as session:  # type: AsyncSession
            result = await session.execute(text("SELECT 1"))
            row = result.scalar()
            return row == 1

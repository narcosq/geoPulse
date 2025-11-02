"""Location repository."""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from decimal import Decimal

from app.internal.repository.repository import Repository
from app.pkg.db.models.location import Location
from app.pkg.db.models.device import Device
from app.pkg.models.schemas.geolocation import LocationCreate, LocationResponse


__all__ = ["LocationRepository"]


class LocationRepository(Repository):
    """Repository for location operations."""

    async def create(self, device_db_id: int, location_data: LocationCreate) -> Location:
        """Create a new location record."""
        async with self._sqlalchemy.session() as session:  # type: AsyncSession
            location = Location(
                device_id=device_db_id,
                latitude=location_data.latitude,
                longitude=location_data.longitude,
                altitude=location_data.altitude,
                accuracy=location_data.accuracy,
                speed=location_data.speed,
                heading=location_data.heading,
                timestamp=location_data.timestamp,
            )
            session.add(location)
            await session.flush()
            await session.refresh(location)
            return location

    async def read_by_id(self, location_id: int) -> Optional[Location]:
        """Read location by ID."""
        async with self._sqlalchemy.session() as session:  # type: AsyncSession
            stmt = select(Location).where(Location.id == location_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def read_latest_by_device_id(self, device_db_id: int) -> Optional[Location]:
        """Read latest location for a device."""
        async with self._sqlalchemy.session() as session:  # type: AsyncSession
            stmt = (
                select(Location)
                .where(Location.device_id == device_db_id)
                .order_by(desc(Location.timestamp))
                .limit(1)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def read_by_device_id(
        self,
        device_db_id: int,
        limit: int = 100,
        offset: int = 0,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Location]:
        """Read locations for a device with pagination and time filtering."""
        async with self._sqlalchemy.session() as session:  # type: AsyncSession
            stmt = select(Location).where(Location.device_id == device_db_id)

            if start_time:
                stmt = stmt.where(Location.timestamp >= start_time)
            if end_time:
                stmt = stmt.where(Location.timestamp <= end_time)

            stmt = stmt.order_by(desc(Location.timestamp)).limit(limit).offset(offset)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update_address(
        self,
        location_id: int,
        address: str,
        city: Optional[str] = None,
        country: Optional[str] = None,
    ) -> None:
        """Update location address information."""
        async with self._sqlalchemy.session() as session:  # type: AsyncSession
            from sqlalchemy import update
            stmt = (
                update(Location)
                .where(Location.id == location_id)
                .values(address=address, city=city, country=country)
            )
            await session.execute(stmt)


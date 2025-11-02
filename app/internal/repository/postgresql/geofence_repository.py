"""Geofence repository."""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from app.internal.repository.repository import Repository
from app.pkg.db.models.geofence import Geofence, DeviceGeofence, GeofenceStatus
from app.pkg.models.schemas.geolocation import GeofenceCreate, GeofenceUpdate


__all__ = ["GeofenceRepository", "DeviceGeofenceRepository"]


class GeofenceRepository(Repository):
    """Repository for geofence operations."""

    async def create(self, geofence_data: GeofenceCreate) -> Geofence:
        """Create a new geofence."""
        async with self._sqlalchemy.session() as session:  # type: AsyncSession
            geofence = Geofence(
                user_id=geofence_data.user_id,
                name=geofence_data.name,
                description=geofence_data.description,
                geofence_type=geofence_data.geofence_type,
                center_latitude=geofence_data.center_latitude,
                center_longitude=geofence_data.center_longitude,
                radius_meters=geofence_data.radius_meters,
                polygon_coordinates=geofence_data.polygon_coordinates,
                min_latitude=geofence_data.min_latitude,
                max_latitude=geofence_data.max_latitude,
                min_longitude=geofence_data.min_longitude,
                max_longitude=geofence_data.max_longitude,
                notify_on_enter=geofence_data.notify_on_enter,
                notify_on_exit=geofence_data.notify_on_exit,
                notification_message=geofence_data.notification_message,
                enable_sound=geofence_data.enable_sound,
                enable_push=geofence_data.enable_push,
                enable_telegram=geofence_data.enable_telegram,
                metadata=geofence_data.metadata,
            )
            session.add(geofence)
            await session.flush()
            await session.refresh(geofence)
            return geofence

    async def read_by_id(self, geofence_id: int) -> Optional[Geofence]:
        """Read geofence by ID."""
        async with self._sqlalchemy.session() as session:  # type: AsyncSession
            stmt = select(Geofence).where(Geofence.id == geofence_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def read_by_user_id(self, user_id: str, status: Optional[GeofenceStatus] = None) -> List[Geofence]:
        """Read all geofences for a user."""
        async with self._sqlalchemy.session() as session:  # type: AsyncSession
            stmt = select(Geofence).where(Geofence.user_id == user_id)
            if status:
                stmt = stmt.where(Geofence.status == status)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update(self, geofence_id: int, geofence_data: GeofenceUpdate) -> Optional[Geofence]:
        """Update geofence."""
        async with self._sqlalchemy.session() as session:  # type: AsyncSession
            geofence = await self.read_by_id(geofence_id)
            if not geofence:
                return None

            update_data = geofence_data.model_dump(exclude_unset=True)
            stmt = update(Geofence).where(Geofence.id == geofence_id).values(**update_data)
            await session.execute(stmt)
            await session.refresh(geofence)
            return geofence

    async def delete(self, geofence_id: int) -> bool:
        """Delete geofence."""
        async with self._sqlalchemy.session() as session:  # type: AsyncSession
            geofence = await self.read_by_id(geofence_id)
            if not geofence:
                return False
            await session.delete(geofence)
            return True


class DeviceGeofenceRepository(Repository):
    """Repository for device-geofence relationship operations."""

    async def get_or_create(self, device_id: int, geofence_id: int) -> DeviceGeofence:
        """Get or create device-geofence relationship."""
        async with self._sqlalchemy.session() as session:  # type: AsyncSession
            stmt = select(DeviceGeofence).where(
                DeviceGeofence.device_id == device_id,
                DeviceGeofence.geofence_id == geofence_id,
            )
            result = await session.execute(stmt)
            device_geofence = result.scalar_one_or_none()

            if not device_geofence:
                device_geofence = DeviceGeofence(
                    device_id=device_id,
                    geofence_id=geofence_id,
                    is_inside=False,
                )
                session.add(device_geofence)
                await session.flush()
                await session.refresh(device_geofence)

            return device_geofence

    async def update_state(
        self,
        device_id: int,
        geofence_id: int,
        is_inside: bool,
        entered_at: Optional[datetime] = None,
        exited_at: Optional[datetime] = None,
    ) -> Optional[DeviceGeofence]:
        """Update device-geofence state."""
        from datetime import datetime, timezone
        from sqlalchemy import update
        async with self._sqlalchemy.session() as session:  # type: AsyncSession
            device_geofence = await self.get_or_create(device_id, geofence_id)

            update_data = {"is_inside": is_inside}
            if entered_at:
                update_data["last_entered_at"] = entered_at
            if exited_at:
                update_data["last_exited_at"] = exited_at

            stmt = (
                update(DeviceGeofence)
                .where(
                    DeviceGeofence.device_id == device_id,
                    DeviceGeofence.geofence_id == geofence_id,
                )
                .values(**update_data)
            )
            await session.execute(stmt)
            await session.refresh(device_geofence)
            return device_geofence

    async def get_by_device_id(self, device_id: int) -> List[DeviceGeofence]:
        """Get all device-geofence relationships for a device."""
        async with self._sqlalchemy.session() as session:  # type: AsyncSession
            stmt = select(DeviceGeofence).where(DeviceGeofence.device_id == device_id)
            result = await session.execute(stmt)
            return list(result.scalars().all())


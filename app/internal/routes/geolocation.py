"""Geolocation API endpoints."""
from typing import List, Optional
from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, status, Depends, HTTPException, Query
from datetime import datetime

from app.pkg.models.schemas.geolocation import (
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    LocationCreate,
    LocationResponse,
    GeofenceCreate,
    GeofenceUpdate,
    GeofenceResponse,
    NotificationCreate,
    NotificationResponse,
    PaginationParams,
)
from app.pkg.models.schemas.pagination import PaginatedResponse
from app.internal import services, repositories
from app.internal.services.geolocation_service import GeolocationService
from app.internal.repository.postgresql import (
    DeviceRepository,
    LocationRepository,
    GeofenceRepository,
    NotificationRepository,
)

router = APIRouter(
    prefix="/api/v1",
    tags=["Geolocation"],
)


# ──────────────────────────────────────────────
# Device endpoints
# ──────────────────────────────────────────────

@router.post("/devices", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
@inject
async def create_device(
    device_data: DeviceCreate,
    device_repo: DeviceRepository = Depends(Provide[repositories.Repositories.postgres.device_repository]),
):
    """Create a new device."""
    device = await device_repo.create(device_data)
    return DeviceResponse.model_validate(device)


@router.get("/devices/{device_id}", response_model=DeviceResponse)
@inject
async def get_device(
    device_id: str,
    device_repo: DeviceRepository = Depends(Provide[repositories.Repositories.postgres.device_repository]),
):
    """Get device by device_id."""
    device = await device_repo.read_by_device_id(device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return DeviceResponse.model_validate(device)


@router.get("/users/{user_id}/devices", response_model=List[DeviceResponse])
@inject
async def get_user_devices(
    user_id: str,
    device_repo: DeviceRepository = Depends(Provide[repositories.Repositories.postgres.device_repository]),
):
    """Get all devices for a user."""
    devices = await device_repo.read_by_user_id(user_id)
    return [DeviceResponse.model_validate(d) for d in devices]


@router.patch("/devices/{device_id}", response_model=DeviceResponse)
@inject
async def update_device(
    device_id: str,
    device_data: DeviceUpdate,
    device_repo: DeviceRepository = Depends(Provide[repositories.Repositories.postgres.device_repository]),
):
    """Update device."""
    device = await device_repo.update(device_id, device_data)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return DeviceResponse.model_validate(device)


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_device(
    device_id: str,
    device_repo: DeviceRepository = Depends(Provide[repositories.Repositories.postgres.device_repository]),
):
    """Delete device."""
    success = await device_repo.delete(device_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")


# ──────────────────────────────────────────────
# Location endpoints
# ──────────────────────────────────────────────

@router.post("/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
@inject
async def create_location(
    location_data: LocationCreate,
    geo_service: GeolocationService = Depends(Provide[services.Services.geolocation]),
):
    """Create a new location and process geofences."""
    await geo_service.process_location(location_data.device_id, location_data)
    
    # Get the created location
    device = await geo_service.device_repository.read_by_device_id(location_data.device_id)
    if device:
        location = await geo_service.location_repository.read_latest_by_device_id(device.id)
        if location:
            return LocationResponse.model_validate(location)
    
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create location")


@router.get("/devices/{device_id}/locations", response_model=List[LocationResponse])
@inject
async def get_device_locations(
    device_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    device_repo: DeviceRepository = Depends(Provide[repositories.Repositories.postgres.device_repository]),
    location_repo: LocationRepository = Depends(Provide[repositories.Repositories.postgres.location_repository]),
):
    """Get locations for a device."""
    device = await device_repo.read_by_device_id(device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    
    locations = await location_repo.read_by_device_id(
        device.id, limit=limit, offset=offset, start_time=start_time, end_time=end_time
    )
    return [LocationResponse.model_validate(l) for l in locations]


# ──────────────────────────────────────────────
# Geofence endpoints
# ──────────────────────────────────────────────

@router.post("/geofences", response_model=GeofenceResponse, status_code=status.HTTP_201_CREATED)
@inject
async def create_geofence(
    geofence_data: GeofenceCreate,
    geofence_repo: GeofenceRepository = Depends(Provide[repositories.Repositories.postgres.geofence_repository]),
):
    """Create a new geofence."""
    geofence = await geofence_repo.create(geofence_data)
    return GeofenceResponse.model_validate(geofence)


@router.get("/geofences/{geofence_id}", response_model=GeofenceResponse)
@inject
async def get_geofence(
    geofence_id: int,
    geofence_repo: GeofenceRepository = Depends(Provide[repositories.Repositories.postgres.geofence_repository]),
):
    """Get geofence by ID."""
    geofence = await geofence_repo.read_by_id(geofence_id)
    if not geofence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Geofence not found")
    return GeofenceResponse.model_validate(geofence)


@router.get("/users/{user_id}/geofences", response_model=List[GeofenceResponse])
@inject
async def get_user_geofences(
    user_id: str,
    geofence_repo: GeofenceRepository = Depends(Provide[repositories.Repositories.postgres.geofence_repository]),
):
    """Get all geofences for a user."""
    geofences = await geofence_repo.read_by_user_id(user_id)
    return [GeofenceResponse.model_validate(g) for g in geofences]


@router.patch("/geofences/{geofence_id}", response_model=GeofenceResponse)
@inject
async def update_geofence(
    geofence_id: int,
    geofence_data: GeofenceUpdate,
    geofence_repo: GeofenceRepository = Depends(Provide[repositories.Repositories.postgres.geofence_repository]),
):
    """Update geofence."""
    geofence = await geofence_repo.update(geofence_id, geofence_data)
    if not geofence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Geofence not found")
    return GeofenceResponse.model_validate(geofence)


@router.delete("/geofences/{geofence_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_geofence(
    geofence_id: int,
    geofence_repo: GeofenceRepository = Depends(Provide[repositories.Repositories.postgres.geofence_repository]),
):
    """Delete geofence."""
    success = await geofence_repo.delete(geofence_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Geofence not found")


# ──────────────────────────────────────────────
# Notification endpoints
# ──────────────────────────────────────────────

@router.post("/notifications", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
@inject
async def create_notification(
    notification_data: NotificationCreate,
    device_repo: DeviceRepository = Depends(Provide[repositories.Repositories.postgres.device_repository]),
    notification_repo: NotificationRepository = Depends(Provide[repositories.Repositories.postgres.notification_repository]),
):
    """Create a new notification."""
    device = await device_repo.read_by_device_id(notification_data.device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    
    notification = await notification_repo.create(device.id, notification_data)
    
    # Queue Celery task
    from tasks.notification_tasks import send_notification_task
    
    send_notification_task.delay(
        notification_id=notification.id,
        device_id=device.device_id,
        notification_type=notification_data.notification_type.value,
        title=notification_data.title,
        message=notification_data.message,
        fcm_token=device.fcm_token,
        telegram_chat_id=device.telegram_chat_id,
        enable_sound=notification_data.enable_sound,
        location_data=notification_data.location_data,
    )
    
    return NotificationResponse.model_validate(notification)


@router.get("/devices/{device_id}/notifications", response_model=List[NotificationResponse])
@inject
async def get_device_notifications(
    device_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    device_repo: DeviceRepository = Depends(Provide[repositories.Repositories.postgres.device_repository]),
    notification_repo: NotificationRepository = Depends(Provide[repositories.Repositories.postgres.notification_repository]),
):
    """Get notifications for a device."""
    device = await device_repo.read_by_device_id(device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    
    notifications = await notification_repo.read_by_device_id(device.id, limit=limit, offset=offset)
    return [NotificationResponse.model_validate(n) for n in notifications]


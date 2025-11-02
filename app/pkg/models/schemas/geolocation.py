"""Schemas for geolocation API."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import Field
from decimal import Decimal

from app.pkg.models.base import BaseModel


# ──────────────────────────────────────────────
# Device Schemas
# ──────────────────────────────────────────────

from enum import Enum


class DevicePlatformModel(str, Enum):
    """Device platform."""
    ANDROID = "android"
    IOS = "ios"
    WEB = "web"


class DeviceStatusModel(str, Enum):
    """Device status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class DeviceCreate(BaseModel):
    """Schema for creating a device."""
    device_id: str = Field(..., description="Unique device identifier")
    user_id: str = Field(..., description="User identifier")
    name: Optional[str] = Field(None, description="Device name")
    platform: DevicePlatformModel = Field(..., description="Device platform")
    fcm_token: Optional[str] = Field(None, description="Firebase Cloud Messaging token")
    apns_token: Optional[str] = Field(None, description="Apple Push Notification Service token")
    telegram_chat_id: Optional[str] = Field(None, description="Telegram chat ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional device metadata")


class DeviceUpdate(BaseModel):
    """Schema for updating a device."""
    name: Optional[str] = Field(None, description="Device name")
    fcm_token: Optional[str] = Field(None, description="Firebase Cloud Messaging token")
    apns_token: Optional[str] = Field(None, description="Apple Push Notification Service token")
    telegram_chat_id: Optional[str] = Field(None, description="Telegram chat ID")
    status: Optional[DeviceStatusModel] = Field(None, description="Device status")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional device metadata")


class DeviceResponse(BaseModel):
    """Schema for device response."""
    id: int
    device_id: str
    user_id: str
    name: Optional[str]
    platform: DevicePlatformModel
    status: DeviceStatusModel
    fcm_token: Optional[str]
    apns_token: Optional[str]
    telegram_chat_id: Optional[str]
    metadata: Optional[Dict[str, Any]]
    last_seen: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# ──────────────────────────────────────────────
# Location Schemas
# ──────────────────────────────────────────────

class LocationCreate(BaseModel):
    """Schema for creating a location."""
    device_id: str = Field(..., description="Device identifier")
    latitude: Decimal = Field(..., ge=-90, le=90, description="Latitude")
    longitude: Decimal = Field(..., ge=-180, le=180, description="Longitude")
    altitude: Optional[Decimal] = Field(None, description="Altitude in meters")
    accuracy: Optional[Decimal] = Field(None, description="Location accuracy in meters")
    speed: Optional[Decimal] = Field(None, description="Speed in m/s")
    heading: Optional[Decimal] = Field(None, ge=0, le=360, description="Heading in degrees")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Location timestamp")


class LocationResponse(BaseModel):
    """Schema for location response."""
    id: int
    device_id: int
    latitude: Decimal
    longitude: Decimal
    altitude: Optional[Decimal]
    accuracy: Optional[Decimal]
    speed: Optional[Decimal]
    heading: Optional[Decimal]
    address: Optional[str]
    city: Optional[str]
    country: Optional[str]
    timestamp: datetime
    created_at: datetime


# ──────────────────────────────────────────────
# Geofence Schemas
# ──────────────────────────────────────────────

class GeofenceTypeModel(str, Enum):
    """Geofence type."""
    CIRCLE = "circle"
    POLYGON = "polygon"
    RECTANGLE = "rectangle"


class GeofenceStatusModel(str, Enum):
    """Geofence status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class GeofenceCreate(BaseModel):
    """Schema for creating a geofence."""
    user_id: str = Field(..., description="User identifier")
    name: str = Field(..., description="Geofence name")
    description: Optional[str] = Field(None, description="Geofence description")
    geofence_type: GeofenceTypeModel = Field(..., description="Type of geofence")
    
    # Circle fields
    center_latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    center_longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    radius_meters: Optional[Decimal] = Field(None, gt=0)
    
    # Polygon fields
    polygon_coordinates: Optional[List[List[Decimal]]] = Field(None, description="List of [lat, lng] pairs")
    
    # Rectangle fields
    min_latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    max_latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    min_longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    max_longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    
    # Notification settings
    notify_on_enter: bool = Field(True, description="Notify when device enters geofence")
    notify_on_exit: bool = Field(True, description="Notify when device exits geofence")
    notification_message: Optional[str] = Field(None, description="Custom notification message")
    enable_sound: bool = Field(True, description="Enable sound notification")
    enable_push: bool = Field(True, description="Enable push notification")
    enable_telegram: bool = Field(False, description="Enable Telegram notification")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class GeofenceUpdate(BaseModel):
    """Schema for updating a geofence."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[GeofenceStatusModel] = None
    notify_on_enter: Optional[bool] = None
    notify_on_exit: Optional[bool] = None
    notification_message: Optional[str] = None
    enable_sound: Optional[bool] = None
    enable_push: Optional[bool] = None
    enable_telegram: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class GeofenceResponse(BaseModel):
    """Schema for geofence response."""
    id: int
    user_id: str
    name: str
    description: Optional[str]
    geofence_type: GeofenceTypeModel
    center_latitude: Optional[Decimal]
    center_longitude: Optional[Decimal]
    radius_meters: Optional[Decimal]
    polygon_coordinates: Optional[List[List[Decimal]]]
    min_latitude: Optional[Decimal]
    max_latitude: Optional[Decimal]
    min_longitude: Optional[Decimal]
    max_longitude: Optional[Decimal]
    status: GeofenceStatusModel
    notify_on_enter: bool
    notify_on_exit: bool
    notification_message: Optional[str]
    enable_sound: bool
    enable_push: bool
    enable_telegram: bool
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class DeviceGeofenceResponse(BaseModel):
    """Schema for device-geofence relationship response."""
    id: int
    device_id: int
    geofence_id: int
    is_inside: bool
    last_entered_at: Optional[datetime]
    last_exited_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# ──────────────────────────────────────────────
# Notification Schemas
# ──────────────────────────────────────────────

class NotificationTypeModel(str, Enum):
    """Notification type."""
    PUSH = "push"
    TELEGRAM = "telegram"
    SMS = "sms"
    EMAIL = "email"


class NotificationStatusModel(str, Enum):
    """Notification status."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"


class NotificationPriorityModel(str, Enum):
    """Notification priority."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationCreate(BaseModel):
    """Schema for creating a notification."""
    device_id: str = Field(..., description="Device identifier")
    notification_type: NotificationTypeModel = Field(..., description="Type of notification")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    priority: NotificationPriorityModel = Field(NotificationPriorityModel.NORMAL, description="Notification priority")
    enable_sound: bool = Field(True, description="Enable sound")
    geofence_id: Optional[int] = Field(None, description="Related geofence ID")
    event_type: Optional[str] = Field(None, description="Event type (e.g., geofence_enter)")
    location_data: Optional[Dict[str, Any]] = Field(None, description="Location data")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled send time")


class NotificationResponse(BaseModel):
    """Schema for notification response."""
    id: int
    device_id: int
    geofence_id: Optional[int]
    notification_type: NotificationTypeModel
    title: str
    message: str
    priority: NotificationPriorityModel
    enable_sound: bool
    status: NotificationStatusModel
    event_type: Optional[str]
    location_data: Optional[Dict[str, Any]]
    fcm_message_id: Optional[str]
    telegram_message_id: Optional[str]
    error_message: Optional[str]
    retry_count: int
    scheduled_at: Optional[datetime]
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class NotificationLogResponse(BaseModel):
    """Schema for notification log response."""
    id: int
    notification_id: int
    action: str
    details: Optional[Dict[str, Any]]
    error_message: Optional[str]
    created_at: datetime


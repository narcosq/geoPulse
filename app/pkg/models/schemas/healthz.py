"""Schemas for health check endpoints."""

from datetime import datetime
from typing import Dict, Any
from pydantic import Field
from enum import Enum

from app.pkg.models.base import BaseModel


# ──────────────────────────────────────────────
# Status Enum
# ──────────────────────────────────────────────

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


# ──────────────────────────────────────────────
# Health Check
# ──────────────────────────────────────────────

class HealthCheckFields:
    """Fields for HealthCheckResponse."""
    status = Field(description="Общее состояние системы",
                   examples=[HealthStatus.HEALTHY, HealthStatus.UNHEALTHY])
    timestamp = Field(description="Время проверки", examples=[datetime.utcnow().isoformat()])
    version = Field(description="Версия приложения", examples=["1.0.0"])
    uptime = Field(description="Время работы приложения (секунды)", examples=[1234.56])
    checks = Field(description="Подробные результаты проверок (DB, Redis, external)",
                   examples=[{
                       "database": {"status": "healthy", "message": "Connection OK"},
                       "redis": {"status": "healthy", "message": "Ping OK"},
                   }])


class HealthCheckResponse(BaseModel):
    """Полный отчёт о состоянии системы."""
    status: HealthStatus = HealthCheckFields.status
    timestamp: str = HealthCheckFields.timestamp
    version: str = HealthCheckFields.version
    uptime: float = HealthCheckFields.uptime
    checks: Dict[str, Dict[str, Any]] = HealthCheckFields.checks


# ──────────────────────────────────────────────
# Liveness
# ──────────────────────────────────────────────

class LivenessFields:
    """Fields for LivenessResponse."""
    status = Field(description="Состояние приложения (живое/нет)",
                   examples=[HealthStatus.HEALTHY])
    timestamp = Field(description="Время проверки", examples=[datetime.utcnow().isoformat()])


class LivenessResponse(BaseModel):
    """Результат liveness probe."""
    status: HealthStatus = LivenessFields.status
    timestamp: str = LivenessFields.timestamp


# ──────────────────────────────────────────────
# Readiness
# ──────────────────────────────────────────────

class ReadinessFields:
    """Fields for ReadinessResponse."""
    status = Field(description="Готовность обрабатывать запросы",
                   examples=[HealthStatus.HEALTHY, HealthStatus.UNHEALTHY])
    timestamp = Field(description="Время проверки", examples=[datetime.utcnow().isoformat()])
    checks = Field(description="Критические проверки (DB, Redis)",
                   examples=[{
                       "database": {"status": "healthy", "message": "Connection OK"},
                       "redis": {"status": "healthy", "message": "Ping OK"}
                   }])


class ReadinessResponse(BaseModel):
    """Результат readiness probe."""
    status: HealthStatus = ReadinessFields.status
    timestamp: str = ReadinessFields.timestamp
    checks: Dict[str, Dict[str, Any]] = ReadinessFields.checks

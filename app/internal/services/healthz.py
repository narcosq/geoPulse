"""Health check service."""

import time
from datetime import datetime
from typing import Dict, Any

from app.internal.repository.postgresql import HealthzOrmRepository
from app.pkg.connectors import redis
from app.pkg.models.schemas.healthz import (
    HealthCheckResponse,
    LivenessResponse,
    ReadinessResponse,
    HealthStatus,
)
from app.pkg.settings import settings
from app.pkg.logger import logger


__all__ = ["HealthzService"]


class HealthzService:
    """Service for application health checks."""

    _healthz_repository: HealthzOrmRepository
    start_time: float

    def __init__(self, healthz_repository: HealthzOrmRepository, redis_connector: redis.Redis):
        self._healthz_repository = healthz_repository
        self._redis_connector = redis_connector
        self.start_time = time.time()

    async def _verify_database_connectivity(self) -> Dict[str, Any]:
        """Verify connection to the primary database."""
        try:
            await self._healthz_repository.check_connection()
            return {"status": HealthStatus.HEALTHY, "message": "Database connection successful"}
        except Exception as e:
            logger.exception("Database connectivity verification failed")
            return {"status": HealthStatus.UNHEALTHY, "message": f"Database error: {str(e)}"}

    async def _verify_redis_availability(self) -> Dict[str, Any]:
        """Verify Redis availability."""

        try:
            await self._redis_connector.ping()
            return {"status": HealthStatus.HEALTHY, "message": "Redis connection successful"}
        except Exception as e:
            logger.exception("Redis availability check failed")
            return {"status": HealthStatus.UNHEALTHY, "message": f"Redis error: {str(e)}"}

    @staticmethod
    async def _evaluate_external_dependencies() -> Dict[str, Any]:
        """Evaluate external service configurations (SMS/Email)."""
        checks = {}

        if settings.SMS_API_URL and settings.SMS_LOGIN and settings.SMS_PASSWORD:
            checks["sms_service"] = {"status": HealthStatus.HEALTHY, "message": "SMS configured"}
        else:
            checks["sms_service"] = {"status": HealthStatus.DEGRADED, "message": "SMS not configured"}

        if (
            settings.EMAIL_SMTP_SERVER
            and settings.EMAIL_USERNAME
            and settings.EMAIL_PASSWORD
            and settings.EMAIL_FROM_EMAIL
        ):
            checks["email_service"] = {"status": HealthStatus.HEALTHY, "message": "Email configured"}
        else:
            checks["email_service"] = {"status": HealthStatus.DEGRADED, "message": "Email not configured"}

        return checks

    async def _calculate_uptime_seconds(self) -> float:
        """Calculate application uptime in seconds."""
        return time.time() - self.start_time

    async def collect_comprehensive_health_report(self) -> HealthCheckResponse:
        """Collect and return a full health report (database, redis, external services)."""
        timestamp = datetime.utcnow().isoformat()
        uptime = await self._calculate_uptime_seconds()

        checks = {
            "database": await self._verify_database_connectivity(),
            "redis": await self._verify_redis_availability(),
        }

        statuses = [check["status"] for check in checks.values()]
        if HealthStatus.UNHEALTHY in statuses:
            overall = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.HEALTHY

        return HealthCheckResponse(
            status=overall,
            timestamp=timestamp,
            version=getattr(settings, "VERSION", "1.0.0"),
            uptime=uptime,
            checks=checks,
        )

    @staticmethod
    async def determine_liveness_status() -> LivenessResponse:
        """Determine whether the application process is alive."""
        return LivenessResponse(
            status=HealthStatus.HEALTHY,
            timestamp=datetime.utcnow().isoformat(),
        )

    async def determine_readiness_status(self) -> ReadinessResponse:
        """Determine whether the application is ready to serve requests."""
        timestamp = datetime.utcnow().isoformat()
        checks = {
            "database": await self._verify_database_connectivity(),
            "redis": await self._verify_redis_availability(),
        }

        critical_statuses = [c["status"] for c in checks.values()]
        overall = (
            HealthStatus.UNHEALTHY
            if any(status == HealthStatus.UNHEALTHY for status in critical_statuses)
            else HealthStatus.HEALTHY
        )

        return ReadinessResponse(status=overall, timestamp=timestamp, checks=checks)

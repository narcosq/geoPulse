"""Health check API endpoints."""

from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, status, Depends, HTTPException

from app.pkg import models
from app.pkg.localization import get_translator, Language

from app.internal import services
from app.internal.services.healthz import HealthzService

# Get translator instance
translator = get_translator()


def _get_localized_tags():
    return [translator.t("api.healthz.title", Language.RU)]


router = APIRouter(
    prefix="/healthz",
    tags=_get_localized_tags(),
    include_in_schema=False,
)


@router.get(
    "/",
    responses={
        status.HTTP_200_OK: models.HealthCheckResponse.model_json_schema(),
    },
    status_code=status.HTTP_200_OK,
    description="Comprehensive health check (DB, Redis, external services, uptime)",
)
@inject
async def health_check(
    health_service: HealthzService = Depends(
        Provide[services.Services.healthz]
    ),
):
    """Return full health report."""
    return await health_service.collect_comprehensive_health_report()


@router.get(
    "/live",
    responses={
        status.HTTP_200_OK: models.LivenessResponse.model_json_schema(),
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Application is not alive"
        },
    },
    status_code=status.HTTP_200_OK,
    description="Kubernetes liveness probe",
)
@inject
async def liveness_probe(
    health_service: HealthzService = Depends(
        Provide[services.Services.healthz]
    ),
):
    """Return liveness status (is app alive)."""
    response = await health_service.determine_liveness_status()
    if response.status == models.HealthStatus.HEALTHY:
        return response
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Application is not alive")


@router.get(
    "/ready",
    responses={
        status.HTTP_200_OK: models.ReadinessResponse.model_json_schema(),
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Application is not ready"
        },
    },
    status_code=status.HTTP_200_OK,
    description="Kubernetes readiness probe",
)
@inject
async def readiness_probe(
    health_service: HealthzService = Depends(
        Provide[services.Services.healthz]
    ),
):
    """Return readiness status (can app handle requests)."""
    response = await health_service.determine_readiness_status()
    if response.status == models.HealthStatus.HEALTHY:
        return response
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Application is not ready")


@router.get(
    "/startup",
    responses={
        status.HTTP_200_OK: models.LivenessResponse.model_json_schema(),
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Application startup failed"
        },
    },
    status_code=status.HTTP_200_OK,
    description="Kubernetes startup probe (is app fully started)",
)
@inject
async def startup_probe(
    health_service: HealthzService = Depends(
        Provide[services.Services.healthz]
    ),
):
    """Return startup probe status."""
    response = await health_service.determine_liveness_status()
    if response.status == models.HealthStatus.HEALTHY:
        return response
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Application startup failed")

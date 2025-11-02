"""Celery app configuration."""
from celery import Celery
from app.pkg.settings.settings import get_settings

settings = get_settings()

celery_app = Celery(
    "geopulse",
    broker=settings.CELERY.BROKER_URL,
    backend=settings.CELERY.RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer=settings.CELERY.TASK_SERIALIZER,
    accept_content=settings.CELERY.ACCEPT_CONTENT,
    result_serializer=settings.CELERY.RESULT_SERIALIZER,
    timezone=settings.CELERY.TIMEZONE,
    enable_utc=settings.CELERY.ENABLE_UTC,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

__all__ = ["celery_app"]


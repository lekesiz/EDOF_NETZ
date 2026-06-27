from __future__ import annotations

from celery import Celery

from .config import get_settings

settings = get_settings()

celery_app = Celery(
    "edof_netz",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["edof_netz.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Paris",
    enable_utc=True,
    beat_schedule={
        "health-check-task": {
            "task": "edof_netz.tasks.health_check_task",
            "schedule": 60.0,
        },
    },
)


@celery_app.task
def health_check_task() -> str:
    return "celery-worker-ok"

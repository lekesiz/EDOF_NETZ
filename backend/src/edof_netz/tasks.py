# mypy: disable-error-code=untyped-decorator
from __future__ import annotations

from typing import Any

from celery import Celery, Task  # type: ignore[import-untyped]

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
        "wedof-full-sync": {
            "task": "edof_netz.tasks.sync_wedof_task",
            "schedule": 15 * 60.0,
            "kwargs": {"limit": 100},
        },
    },
)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def health_check_task(_self: Task) -> str:
    return "celery-worker-ok"


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def sync_wedof_task(
    _self: Task,
    entity_types: list[str] | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Run a full or partial Wedof synchronisation.

    Supported entity_types: attendees, trainings, training_actions,
    registration_folders, certification_folders.
    """
    from .services.wedof import (
        sync_attendees,
        sync_certification_folders,
        sync_registration_folders,
        sync_training_actions,
        sync_trainings,
    )

    mappers = {
        "attendees": sync_attendees,
        "trainings": sync_trainings,
        "training_actions": sync_training_actions,
        "registration_folders": sync_registration_folders,
        "certification_folders": sync_certification_folders,
    }

    selected = entity_types or list(mappers.keys())
    results: dict[str, Any] = {}
    for key in selected:
        if key not in mappers:
            continue
        try:
            results.update(mappers[key](limit=limit))
        except Exception as exc:  # noqa: BLE001
            _self.retry(exc=exc)
    return results


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def sync_attendees_task(_self: Task, limit: int = 100) -> dict[str, Any]:
    from .services.wedof import sync_attendees

    return sync_attendees(limit=limit)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def refresh_registration_folder_task(
    _self: Task,
    external_id: str,
) -> dict[str, Any]:
    from .services.wedof import refresh_registration_folder

    try:
        return refresh_registration_folder(external_id)
    except Exception as exc:  # noqa: BLE001
        _self.retry(exc=exc)
    return {}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def refresh_certification_folder_task(
    _self: Task,
    external_id: str,
) -> dict[str, Any]:
    from .services.wedof import refresh_certification_folder

    try:
        return refresh_certification_folder(external_id)
    except Exception as exc:  # noqa: BLE001
        _self.retry(exc=exc)
    return {}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def process_wedof_webhook_task(_self: Task, event_id: str) -> dict[str, Any]:
    from .services.wedof import process_webhook_event

    try:
        return process_webhook_event(event_id)
    except Exception as exc:  # noqa: BLE001
        _self.retry(exc=exc)
    return {}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def push_pennylane_invoice_task(
    _self: Task,
    registration_folder_external_id: str,
    draft: bool = True,
) -> dict[str, Any]:
    from .services.pennylane import push_registration_folder_as_invoice

    try:
        return push_registration_folder_as_invoice(
            registration_folder_external_id,
            draft=draft,
        )
    except Exception as exc:  # noqa: BLE001
        _self.retry(exc=exc)
    return {}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def push_all_pennylane_invoices_task(_self: Task, draft: bool = True, limit: int = 100) -> dict[str, Any]:
    from .services.pennylane import push_all_invoices

    try:
        return push_all_invoices(draft=draft, limit=limit)
    except Exception as exc:  # noqa: BLE001
        _self.retry(exc=exc)
    return {}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def sync_pennylane_invoices_task(_self: Task, limit: int = 100) -> dict[str, Any]:
    from .services.pennylane import sync_invoices_from_pennylane

    try:
        return sync_invoices_from_pennylane(limit=limit)
    except Exception as exc:  # noqa: BLE001
        _self.retry(exc=exc)
    return {}

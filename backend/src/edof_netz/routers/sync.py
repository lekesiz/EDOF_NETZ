from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ..auth import require_role
from ..models import User, UserRole
from ..tasks import sync_wedof_task

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/wedof")
def trigger_wedof_sync(
    entity_types: list[str] | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    _current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPERUSER, UserRole.ACCOUNTANT)),
) -> dict[str, str]:
    """Trigger a Wedof synchronisation task.

    Available entity types: attendees, trainings, training_actions,
    registration_folders, certification_folders.
    """
    task = sync_wedof_task.delay(entity_types=entity_types, limit=limit)
    return {"status": "started", "task_id": task.id}

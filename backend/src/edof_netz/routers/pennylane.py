from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ..auth import require_role
from ..models import User, UserRole
from ..tasks import (
    push_all_pennylane_invoices_task,
    push_pennylane_invoice_task,
    sync_pennylane_invoices_task,
)

router = APIRouter(prefix="/pennylane", tags=["pennylane"])


@router.post("/push/invoices")
def trigger_push_all_pennylane_invoices(
    draft: bool = Query(True),
    limit: int = Query(100, ge=1, le=500),
    _current_user: User = Depends(
        require_role(UserRole.ADMIN, UserRole.SUPERUSER, UserRole.ACCOUNTANT)
    ),
) -> dict[str, str]:
    """Push Wedof registration folders to Pennylane as customer invoices."""
    task = push_all_pennylane_invoices_task.delay(draft=draft, limit=limit)
    return {"status": "started", "task_id": task.id}


@router.post("/push/invoices/{registration_folder_external_id}")
def trigger_push_single_pennylane_invoice(
    registration_folder_external_id: str,
    draft: bool = Query(True),
    _current_user: User = Depends(
        require_role(UserRole.ADMIN, UserRole.SUPERUSER, UserRole.ACCOUNTANT)
    ),
) -> dict[str, str]:
    """Push a single registration folder to Pennylane as a customer invoice."""
    task = push_pennylane_invoice_task.delay(
        registration_folder_external_id,
        draft=draft,
    )
    return {"status": "started", "task_id": task.id}


@router.post("/sync/invoices")
def trigger_sync_pennylane_invoices(
    limit: int = Query(100, ge=1, le=500),
    _current_user: User = Depends(
        require_role(UserRole.ADMIN, UserRole.SUPERUSER, UserRole.ACCOUNTANT)
    ),
) -> dict[str, str]:
    """Pull customer invoices from Pennylane into the local database."""
    task = sync_pennylane_invoices_task.delay(limit=limit)
    return {"status": "started", "task_id": task.id}

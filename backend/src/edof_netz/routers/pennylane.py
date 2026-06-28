from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from ..auth import require_role
from ..db import engine
from ..models import Attendee, User, UserRole
from ..schemas import AttendeeListItem, InvoiceableCandidateItem
from ..services.pennylane import get_invoiceable_folders
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


@router.get("/candidates", response_model=list[InvoiceableCandidateItem])
def list_invoiceable_candidates(
    target_date: date | None = Query(None),
    billing_state: str = Query("toBill"),
    limit: int = Query(100, ge=1, le=500),
    _current_user: User = Depends(
        require_role(UserRole.ADMIN, UserRole.SUPERUSER, UserRole.ACCOUNTANT)
    ),
) -> list[InvoiceableCandidateItem]:
    """List registration folders that are ready to be invoiced for the selected date."""
    folders = get_invoiceable_folders(
        target_date=target_date, billing_state=billing_state, limit=limit
    )
    items: list[InvoiceableCandidateItem] = []
    with Session(engine) as session:
        for folder in folders:
            attendee = (
                session.get(Attendee, folder.attendee_id)
                if folder.attendee_id
                else None
            )
            items.append(
                InvoiceableCandidateItem(
                    id=folder.id,
                    external_id=folder.external_id,
                    state=folder.state,
                    billing_state=folder.billing_state,
                    amount_ttc=folder.amount_ttc,
                    amount_ht=folder.amount_ht,
                    created_on=folder.created_on.isoformat() if folder.created_on else None,
                    training_action_external_id=folder.training_action_external_id,
                    attendee=AttendeeListItem.model_validate(
                        attendee, from_attributes=True
                    )
                    if attendee
                    else None,
                )
            )
    return items


@router.get("/candidates/count")
def count_invoiceable_candidates(
    target_date: date | None = Query(None),
    billing_state: str = Query("toBill"),
    limit: int = Query(1000, ge=1, le=5000),
    _current_user: User = Depends(
        require_role(UserRole.ADMIN, UserRole.SUPERUSER, UserRole.ACCOUNTANT)
    ),
) -> dict[str, int]:
    """Return the number of registration folders ready to be invoiced."""
    folders = get_invoiceable_folders(
        target_date=target_date, billing_state=billing_state, limit=limit
    )
    return {"count": len(folders)}


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

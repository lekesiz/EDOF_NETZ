# mypy: disable-error-code="attr-defined,arg-type,index,union-attr"
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlmodel import Session, select

from ..auth import get_current_user
from ..db import get_session
from ..models import Attendee, CertificationFolder, Invoice, RegistrationFolder, User
from ..schemas import (
    AttendeeListItem,
    CertificationFolderListItem,
    RegistrationFolderListItem,
)

router = APIRouter(prefix="/folders", tags=["folders"])


@router.get("/registration", response_model=list[RegistrationFolderListItem])
def list_registration_folders(
    state: str | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
    _current_user: User = Depends(get_current_user),
) -> list[RegistrationFolder]:
    statement = select(RegistrationFolder)
    if state:
        statement = statement.where(RegistrationFolder.state == state)
    if search:
        statement = statement.where(
            RegistrationFolder.external_id.ilike(f"%{search}%")
            | RegistrationFolder.raw_data["attendee"]["email"].as_string().ilike(f"%{search}%")
        )
    statement = statement.order_by(RegistrationFolder.created_on.desc()).offset(offset).limit(limit)
    return list(session.exec(statement).all())


@router.get("/registration/count")
def count_registration_folders(
    state: str | None = Query(None),
    session: Session = Depends(get_session),
    _current_user: User = Depends(get_current_user),
) -> dict[str, int]:
    statement = select(func.count(RegistrationFolder.id))
    if state:
        statement = statement.where(RegistrationFolder.state == state)
    count = session.exec(statement).one()
    return {"count": count}


@router.get("/certification", response_model=list[CertificationFolderListItem])
def list_certification_folders(
    state: str | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
    _current_user: User = Depends(get_current_user),
) -> list[CertificationFolder]:
    statement = select(CertificationFolder)
    if state:
        statement = statement.where(CertificationFolder.state == state)
    if search:
        statement = statement.where(CertificationFolder.external_id.ilike(f"%{search}%"))
    statement = statement.order_by(CertificationFolder.created_on.desc()).offset(offset).limit(limit)
    return list(session.exec(statement).all())


@router.get("/certification/count")
def count_certification_folders(
    state: str | None = Query(None),
    session: Session = Depends(get_session),
    _current_user: User = Depends(get_current_user),
) -> dict[str, int]:
    statement = select(func.count(CertificationFolder.id))
    if state:
        statement = statement.where(CertificationFolder.state == state)
    count = session.exec(statement).one()
    return {"count": count}


@router.get("/attendees", response_model=list[AttendeeListItem])
def list_attendees(
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
    _current_user: User = Depends(get_current_user),
) -> list[Attendee]:
    statement = select(Attendee)
    if search:
        statement = statement.where(
            Attendee.email.ilike(f"%{search}%")
            | Attendee.first_name.ilike(f"%{search}%")
            | Attendee.last_name.ilike(f"%{search}%")
        )
    statement = statement.order_by(Attendee.created_at.desc()).offset(offset).limit(limit)
    return list(session.exec(statement).all())


@router.get("/attendees/count")
def count_attendees(
    search: str | None = Query(None),
    session: Session = Depends(get_session),
    _current_user: User = Depends(get_current_user),
) -> dict[str, int]:
    statement = select(func.count(Attendee.id))
    if search:
        statement = statement.where(
            Attendee.email.ilike(f"%{search}%")
            | Attendee.first_name.ilike(f"%{search}%")
            | Attendee.last_name.ilike(f"%{search}%")
        )
    count = session.exec(statement).one()
    return {"count": count}


@router.get("/attendees/{attendee_id}/profile")
def get_attendee_profile(
    attendee_id: str,
    session: Session = Depends(get_session),
    _current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Return a single attendee with all related folders and invoices."""
    attendee = session.get(Attendee, attendee_id)
    if attendee is None:
        raise HTTPException(status_code=404, detail="Attendee not found")

    registration_folders = list(
        session.exec(
            select(RegistrationFolder)
            .where(RegistrationFolder.attendee_id == attendee_id)
            .order_by(RegistrationFolder.created_on.desc())
        ).all()
    )
    certification_folders = list(
        session.exec(
            select(CertificationFolder)
            .where(CertificationFolder.attendee_id == attendee_id)
            .order_by(CertificationFolder.created_on.desc())
        ).all()
    )

    reg_external_ids = [f.external_id for f in registration_folders if f.external_id]
    invoices: list[Invoice] = []
    if reg_external_ids:
        invoices = list(
            session.exec(
                select(Invoice)
                .where(Invoice.registration_folder_external_id.in_(reg_external_ids))
                .order_by(Invoice.created_at.desc())
            ).all()
        )

    return {
        "attendee": AttendeeListItem.model_validate(attendee, from_attributes=True),
        "registration_folders": [
            RegistrationFolderListItem.model_validate(f, from_attributes=True)
            for f in registration_folders
        ],
        "certification_folders": [
            CertificationFolderListItem.model_validate(f, from_attributes=True)
            for f in certification_folders
        ],
        "invoices": [
            {
                "id": inv.id,
                "external_id": inv.external_id,
                "state": inv.state,
                "amount_ttc": inv.amount_ttc,
                "amount_ht": inv.amount_ht,
                "due_date": inv.due_date.isoformat() if inv.due_date else None,
                "registration_folder_external_id": inv.registration_folder_external_id,
                "pennylane_invoice_id": inv.pennylane_invoice_id,
                "pennylane_customer_id": inv.pennylane_customer_id,
            }
            for inv in invoices
        ],
    }

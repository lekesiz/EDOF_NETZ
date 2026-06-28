# mypy: disable-error-code="attr-defined,arg-type,index,union-attr"
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlmodel import Session, select

from ..auth import get_current_user
from ..db import get_session
from ..models import Attendee, CertificationFolder, RegistrationFolder, User
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

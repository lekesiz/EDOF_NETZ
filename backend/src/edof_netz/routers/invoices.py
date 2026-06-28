# mypy: disable-error-code="attr-defined,arg-type,index,union-attr"
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlmodel import Session, select

from ..auth import get_current_user
from ..db import get_session
from ..models import Invoice, User
from ..schemas import InvoiceListItem

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("/", response_model=list[InvoiceListItem])
def list_invoices(
    state: str | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
    _current_user: User = Depends(get_current_user),
) -> list[Invoice]:
    statement = select(Invoice)
    if state:
        statement = statement.where(Invoice.state == state)
    if search:
        statement = statement.where(
            Invoice.external_id.ilike(f"%{search}%")
            | Invoice.registration_folder_external_id.ilike(f"%{search}%")
        )
    statement = statement.order_by(Invoice.created_at.desc()).offset(offset).limit(limit)
    return list(session.exec(statement).all())


@router.get("/count")
def count_invoices(
    state: str | None = Query(None),
    session: Session = Depends(get_session),
    _current_user: User = Depends(get_current_user),
) -> dict[str, int]:
    statement = select(func.count(Invoice.id))
    if state:
        statement = statement.where(Invoice.state == state)
    count = session.exec(statement).one()
    return {"count": count}

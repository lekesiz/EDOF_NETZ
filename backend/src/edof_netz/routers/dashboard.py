from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from ..auth import get_current_user, require_role
from ..db import get_session
from ..models import Settings, User, UserRole
from ..schemas import DashboardResponse
from ..services.dashboard import compute_dashboard

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/", response_model=DashboardResponse)
def get_dashboard(
    year: int = Query(default_factory=lambda: datetime.now().year),
    _current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    """Return financial dashboard data for the selected year."""
    return compute_dashboard(year)


@router.get("/settings")
def list_settings(
    session: Session = Depends(get_session),
    _current_user: User = Depends(get_current_user),
) -> list[Settings]:
    """Return all editable dashboard settings."""
    return list(session.exec(select(Settings)).all())


@router.put("/settings/{key}")
def update_setting(
    key: str,
    value: str,
    session: Session = Depends(get_session),
    _current_user: User = Depends(
        require_role(UserRole.ADMIN, UserRole.SUPERUSER, UserRole.ACCOUNTANT)
    ),
) -> dict[str, str]:
    """Update a single dashboard setting (e.g. target_2026 or vade_gun)."""
    row = session.exec(select(Settings).where(Settings.key == key)).first()
    if row is None:
        return {"status": "not_found", "key": key}
    row.value = value
    session.add(row)
    session.commit()
    return {"status": "updated", "key": key, "value": value}

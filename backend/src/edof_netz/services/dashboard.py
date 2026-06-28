from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlmodel import Session, select

from ..db import engine
from ..models import RegistrationFolder, Settings, TrainingAction, WedofSyncState


_CANCELED_KEYWORDS = ["cancel", "refus", "reject", "annul", "abandon"]


def _is_invalidated(state: str | None) -> bool:
    if not state:
        return False
    lower = state.lower()
    return any(kw in lower for kw in _CANCELED_KEYWORDS)


def _setting_value(key: str, default: str) -> str:
    with Session(engine) as session:
        row = session.exec(select(Settings).where(Settings.key == key)).first()
        return row.value if row else default


def get_vade_gun() -> int:
    try:
        return int(_setting_value("vade_gun", "37"))
    except ValueError:
        return 37


def get_target_for_year(year: int) -> float:
    try:
        return float(_setting_value(f"target_{year}", "0"))
    except ValueError:
        return 0.0


def _get_due_date(
    folder: RegistrationFolder, action: TrainingAction | None, vade_gun: int
) -> date | None:
    raw_end = action.end_date if action else None
    if raw_end is None:
        raw_end = folder.created_on
    if raw_end is None:
        return None
    end_date = raw_end.date() if isinstance(raw_end, datetime) else raw_end
    return end_date + timedelta(days=vade_gun)


def _categorize(
    folder: RegistrationFolder,
    action: TrainingAction | None,
    vade_gun: int,
    today: date,
) -> str | None:
    if _is_invalidated(folder.state):
        return "kayip"
    due = _get_due_date(folder, action, vade_gun)
    if due is None:
        return None
    if due <= today:
        return "kasa"
    return "alacak"


def compute_dashboard(year: int) -> dict[str, object]:
    """Compute dashboard stats and monthly breakdown for a given year."""
    vade_gun = get_vade_gun()
    target = get_target_for_year(year)
    today = datetime.now(ZoneInfo("Europe/Paris")).date()

    months: dict[str, dict[str, float]] = {
        f"{year}-{m:02d}": {"kasa": 0.0, "alacak": 0.0, "kayip": 0.0}
        for m in range(1, 13)
    }
    kasa = alacak = kayip = 0.0
    total_dossiers = 0
    reconciled_count = 0

    with Session(engine) as session:
        rows = session.exec(
            select(RegistrationFolder, TrainingAction)
            .outerjoin(
                TrainingAction,
                RegistrationFolder.training_action_external_id == TrainingAction.external_id,  # type: ignore[arg-type]
            )
            .where(
                (RegistrationFolder.amount_ttc.isnot(None))  # type: ignore[union-attr]
                | (RegistrationFolder.amount_ht.isnot(None))  # type: ignore[union-attr]
            )
        ).all()

        for folder, action in rows:
            category = _categorize(folder, action, vade_gun, today)
            if category is None:
                continue
            amount = folder.amount_ttc or folder.amount_ht or 0.0
            if category == "kasa":
                kasa += amount
            elif category == "alacak":
                alacak += amount
            else:
                kayip += amount

            total_dossiers += 1
            if folder.is_reconciled:
                reconciled_count += 1

            due = _get_due_date(folder, action, vade_gun)
            if due and due.year == year:
                key = due.strftime("%Y-%m")
                if key in months:
                    months[key][category] += amount

        realized = kasa + alacak
        effective_target = target if target > 0 else realized

        last_sync: dict[str, str | None] = {}
        for entity_type in ["registration_folders", "certification_folders"]:
            state = session.exec(
                select(WedofSyncState).where(WedofSyncState.entity_type == entity_type)
            ).first()
            last_sync[entity_type] = (
                state.last_sync_at.isoformat() if state and state.last_sync_at else None
            )
        pennylane_state = session.exec(
            select(WedofSyncState).where(WedofSyncState.entity_type == "pennylane")
        ).first()
        last_sync["pennylane"] = (
            pennylane_state.last_sync_at.isoformat()
            if pennylane_state and pennylane_state.last_sync_at
            else None
        )

    return {
        "year": year,
        "stats": {
            "target_amount": effective_target,
            "realized": realized,
            "remaining": max(0.0, effective_target - realized),
            "kasa": kasa,
            "alacak": alacak,
            "kayip": kayip,
            "total_dossiers": total_dossiers,
            "reconciled_count": reconciled_count,
        },
        "monthly_data": [
            {"month": month, **months[month]} for month in sorted(months)
        ],
        "last_sync": last_sync,
    }

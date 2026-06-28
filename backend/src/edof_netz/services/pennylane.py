# mypy: disable-error-code=import-untyped
from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Any

from sqlalchemy import func, or_
from sqlmodel import Session, select
from pennylane_sdk import PennylaneClient

from ..config import get_settings
from ..db import engine
from ..models import Attendee, Invoice, RegistrationFolder

logger = logging.getLogger(__name__)


class PennylaneNotConfiguredError(RuntimeError):
    """Raised when the Pennylane API token is missing."""


_VAT_MULTIPLIERS = {
    "FR_200": 0.20,
    "FR_100": 0.10,
    "FR_055": 0.055,
    "exempt": 0.0,
    "any": 0.0,
}


_CANCELED_STATES = {
    "canceledByAttendee",
    "canceledByAttendeeNotRealized",
    "canceledByOrganism",
    "canceledByFinancer",
    "refusedByAttendee",
    "refusedByOrganism",
    "refusedByFinancer",
    "rejected",
    "rejectedWithoutTitulaireSuite",
    "rejectedWithoutCdcSuite",
    "rejectedWithoutOfSuite",
}


def get_pennylane_client() -> PennylaneClient:
    """Return a configured Pennylane SDK client."""
    settings = get_settings()
    if not settings.pennylane_api_token:
        raise PennylaneNotConfiguredError("PENNYLANE_API_TOKEN is not configured")
    return PennylaneClient(token=settings.pennylane_api_token)


def _to_decimal_str(value: float | None) -> str:
    return f"{(value or 0):.2f}"


def _parse_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _vat_multiplier(vat_rate: str) -> float:
    return _VAT_MULTIPLIERS.get(vat_rate, 0.20)


def _to_date(value: datetime | date | None) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.now(timezone.utc).date()


def _build_customer_payload(attendee: Attendee) -> dict[str, Any]:
    name = f"{attendee.first_name or ''} {attendee.last_name or ''}".strip() or "Client"
    payload: dict[str, Any] = {
        "external_reference": attendee.id,
        "name": name,
        "first_name": attendee.first_name or "",
        "last_name": attendee.last_name or "",
    }
    if attendee.email:
        payload["emails"] = [attendee.email]
    if attendee.phone_number:
        payload["phone"] = attendee.phone_number
    return payload


def _find_customer_id(client: PennylaneClient, attendee: Attendee) -> str | None:
    """Look up an existing Pennylane customer by attendee id (external_reference)."""
    if attendee.pennylane_customer_id:
        return attendee.pennylane_customer_id

    filter_json = json.dumps(
        [{"field": "external_reference", "operator": "eq", "value": attendee.id}]
    )
    response = client.customers.get_customers(filter=filter_json, limit="10")
    items: list[dict[str, Any]] = []
    if isinstance(response, dict):
        items = response.get("items") or []
    elif isinstance(response, list):
        items = response
    if items:
        return str(items[0].get("id"))
    return None


def _ensure_customer(client: PennylaneClient, session: Session, attendee: Attendee) -> str:
    """Create or update a Pennylane individual customer for the attendee."""
    customer_id = _find_customer_id(client, attendee)
    payload = _build_customer_payload(attendee)
    if customer_id:
        logger.info("Updating Pennylane customer %s for attendee %s", customer_id, attendee.id)
        client.customers.put_individual_customer(id=customer_id, body=payload)
    else:
        logger.info("Creating Pennylane customer for attendee %s", attendee.id)
        response = client.customers.post_individual_customer(body=payload)
        customer_id = str(response["id"])
    attendee.pennylane_customer_id = customer_id
    session.add(attendee)
    return customer_id


def _build_invoice_lines(folder: RegistrationFolder, vat_rate: str) -> list[dict[str, Any]]:
    """Build a single invoice line from the registration folder amount."""
    amount_ttc = folder.amount_ttc or 0.0
    amount_ht = folder.amount_ht
    if amount_ht is None:
        multiplier = 1 + _vat_multiplier(vat_rate)
        amount_ht = amount_ttc / multiplier if multiplier else amount_ttc
    return [
        {
            "label": folder.training_action_external_id or "Formation",
            "quantity": 1,
            "unit": "piece",
            "raw_currency_unit_price": _to_decimal_str(amount_ht),
            "vat_rate": vat_rate,
        }
    ]


def push_registration_folder_as_invoice(
    registration_folder_external_id: str,
    *,
    draft: bool = True,
) -> dict[str, Any]:
    """Push a Wedof registration folder to Pennylane as a customer invoice."""
    settings = get_settings()
    vat_rate = settings.pennylane_default_vat_rate

    with get_pennylane_client() as client, Session(engine) as session:
        folder = session.exec(
            select(RegistrationFolder).where(
                RegistrationFolder.external_id == registration_folder_external_id
            )
        ).first()
        if folder is None:
            return {"status": "not_found", "external_id": registration_folder_external_id}

        if folder.amount_ttc is None and folder.amount_ht is None:
            return {
                "status": "skipped",
                "reason": "missing amount",
                "external_id": registration_folder_external_id,
            }

        if folder.state in _CANCELED_STATES:
            return {
                "status": "skipped",
                "reason": "canceled/refused state",
                "external_id": registration_folder_external_id,
            }

        attendee = session.get(Attendee, folder.attendee_id) if folder.attendee_id else None
        if attendee is None:
            return {
                "status": "skipped",
                "reason": "missing attendee",
                "external_id": registration_folder_external_id,
            }

        customer_id = _ensure_customer(client, session, attendee)
        invoice_date = _to_date(folder.created_on)
        deadline = invoice_date + timedelta(days=30)

        body: dict[str, Any] = {
            "customer_id": int(customer_id),
            "date": invoice_date.isoformat(),
            "deadline": deadline.isoformat(),
            "external_reference": folder.external_id,
            "draft": draft,
            "invoice_lines": _build_invoice_lines(folder, vat_rate),
            "currency": "EUR",
        }

        response = client.customer_invoices.post_customer_invoices(body=body)
        pennylane_invoice_id = str(response.get("id"))

        invoice = session.exec(
            select(Invoice).where(
                Invoice.registration_folder_external_id == folder.external_id
            )
        ).first()
        if invoice is None:
            invoice = Invoice(
                external_id=folder.external_id,
                registration_folder_external_id=folder.external_id,
            )
            session.add(invoice)

        invoice.pennylane_invoice_id = pennylane_invoice_id
        invoice.pennylane_customer_id = customer_id
        invoice.amount_ttc = folder.amount_ttc
        invoice.amount_ht = folder.amount_ht
        invoice.state = response.get("status") or ("draft" if draft else "finalized")
        invoice.due_date = datetime.combine(deadline, datetime.min.time(), tzinfo=timezone.utc)
        invoice.raw_data = response
        session.commit()

    logger.info(
        "Pushed invoice %s to Pennylane for folder %s",
        pennylane_invoice_id,
        folder.external_id,
    )
    return {
        "status": "pushed",
        "external_id": folder.external_id,
        "pennylane_invoice_id": pennylane_invoice_id,
        "draft": draft,
    }


def get_invoiceable_folders(
    target_date: date | None = None,
    billing_state: str = "toBill",
    limit: int = 100,
) -> list[RegistrationFolder]:
    """Return registration folders that are ready to be invoiced today.

    Criteria:
    - billing_state matches the requested value (default "toBill").
    - Has an amount (TTC or HT).
    - Not in a cancelled/refused/rejected state.
    - created_on matches the target date (default today in UTC).
    - Not already pushed to Pennylane.
    """
    if target_date is None:
        target_date = datetime.now(ZoneInfo("Europe/Paris")).date()

    with Session(engine) as session:
        pushed_subquery = select(Invoice.registration_folder_external_id).where(
            Invoice.registration_folder_external_id.isnot(None),  # type: ignore[union-attr]
            Invoice.pennylane_invoice_id.isnot(None),  # type: ignore[union-attr]
        )
        # Compare dates in Europe/Paris because the business day is what matters.
        paris_date = func.date(func.timezone("Europe/Paris", RegistrationFolder.created_on))
        statement = (
            select(RegistrationFolder)
            .where(
                RegistrationFolder.billing_state == billing_state,
                or_(
                    RegistrationFolder.amount_ttc.isnot(None),  # type: ignore[union-attr]
                    RegistrationFolder.amount_ht.isnot(None),  # type: ignore[union-attr]
                ),
                RegistrationFolder.state.notin_(list(_CANCELED_STATES)),  # type: ignore[union-attr]
                paris_date == target_date,
                RegistrationFolder.external_id.notin_(pushed_subquery),  # type: ignore[attr-defined]
            )
            .order_by(RegistrationFolder.created_on.desc())  # type: ignore[union-attr]
            .limit(limit)
        )
        return list(session.exec(statement).all())


def push_all_invoices(*, draft: bool = True, limit: int = 100) -> dict[str, Any]:
    """Push all eligible registration folders as Pennylane invoices."""
    results: list[dict[str, Any]] = []
    with Session(engine) as session:
        statement = (
            select(RegistrationFolder)
            .where(
                or_(
                    RegistrationFolder.amount_ttc.isnot(None),  # type: ignore[union-attr]
                    RegistrationFolder.amount_ht.isnot(None),  # type: ignore[union-attr]
                ),
                RegistrationFolder.state.notin_(list(_CANCELED_STATES)),  # type: ignore[union-attr]
            )
            .order_by(RegistrationFolder.created_on.desc())  # type: ignore[union-attr]
            .limit(limit)
        )
        folders = list(session.exec(statement).all())

    for folder in folders:
        # Skip folders that already have a Pennylane invoice.
        with Session(engine) as session:
            existing = session.exec(
                select(Invoice).where(
                    Invoice.registration_folder_external_id == folder.external_id,
                    Invoice.pennylane_invoice_id.isnot(None),  # type: ignore[union-attr]
                )
            ).first()
            if existing is not None:
                continue
        result = push_registration_folder_as_invoice(folder.external_id, draft=draft)
        results.append(result)

    pushed = [r for r in results if r.get("status") == "pushed"]
    return {"processed": len(results), "pushed": len(pushed), "results": results}


def sync_invoices_from_pennylane(limit: int = 100) -> dict[str, Any]:
    """Pull customer invoices from Pennylane and store them locally."""
    with get_pennylane_client() as client, Session(engine) as session:
        count = 0
        for raw in client.paginate(
            client.customer_invoices.get_customer_invoices,
            limit=str(limit),
        ):
            external_id = raw.get("external_reference") or str(raw.get("id"))
            invoice = session.exec(
                select(Invoice).where(Invoice.external_id == external_id)
            ).first()
            if invoice is None:
                invoice = Invoice(external_id=external_id)
                session.add(invoice)

            invoice.pennylane_invoice_id = str(raw.get("id"))
            invoice.state = raw.get("status")
            customer = raw.get("customer") or {}
            invoice.pennylane_customer_id = (
                str(customer.get("id")) if customer else invoice.pennylane_customer_id
            )
            invoice.amount_ttc = _parse_float(raw.get("currency_amount"))
            invoice.amount_ht = _parse_float(raw.get("currency_amount_before_tax"))
            invoice.raw_data = raw
            count += 1
        session.commit()
    logger.info("Synced %s invoices from Pennylane", count)
    return {"invoices": count}

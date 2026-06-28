from __future__ import annotations

from datetime import date, datetime, timezone

from edof_netz.models import Attendee, RegistrationFolder
from edof_netz.services.pennylane import (
    PennylaneNotConfiguredError,
    _build_customer_payload,
    _build_invoice_lines,
    _parse_float,
    _to_date,
    _to_decimal_str,
    _vat_multiplier,
    get_pennylane_client,
)


def test_to_decimal_str() -> None:
    assert _to_decimal_str(12.5) == "12.50"
    assert _to_decimal_str(None) == "0.00"


def test_parse_float() -> None:
    assert _parse_float("12.34") == 12.34
    assert _parse_float(56) == 56.0
    assert _parse_float(None) is None
    assert _parse_float("abc") is None


def test_vat_multiplier() -> None:
    assert _vat_multiplier("FR_200") == 0.20
    assert _vat_multiplier("exempt") == 0.0
    assert _vat_multiplier("UNKNOWN") == 0.20


def test_to_date() -> None:
    dt = datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)
    assert _to_date(dt) == date(2024, 1, 15)
    assert _to_date(date(2024, 1, 15)) == date(2024, 1, 15)
    assert isinstance(_to_date(None), date)


def test_build_customer_payload() -> None:
    attendee = Attendee(
        id="att-1",
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone_number="+33600000000",
    )
    payload = _build_customer_payload(attendee)
    assert payload["external_reference"] == "att-1"
    assert payload["name"] == "John Doe"
    assert payload["first_name"] == "John"
    assert payload["last_name"] == "Doe"
    assert payload["emails"] == ["john@example.com"]
    assert payload["phone"] == "+33600000000"


def test_build_customer_payload_defaults() -> None:
    attendee = Attendee(id="att-2")
    payload = _build_customer_payload(attendee)
    assert payload["name"] == "Client"
    assert "emails" not in payload
    assert "phone" not in payload


def test_build_invoice_lines_with_ht() -> None:
    folder = RegistrationFolder(external_id="rf-1", amount_ttc=120.0, amount_ht=100.0)
    lines = _build_invoice_lines(folder, "FR_200")
    assert len(lines) == 1
    assert lines[0]["raw_currency_unit_price"] == "100.00"
    assert lines[0]["vat_rate"] == "FR_200"
    assert lines[0]["quantity"] == 1


def test_build_invoice_lines_without_ht() -> None:
    folder = RegistrationFolder(external_id="rf-2", amount_ttc=120.0)
    lines = _build_invoice_lines(folder, "FR_200")
    assert lines[0]["raw_currency_unit_price"] == "100.00"


def test_get_pennylane_client_raises_when_token_missing(monkeypatch) -> None:
    monkeypatch.delenv("PENNYLANE_API_TOKEN", raising=False)
    try:
        get_pennylane_client()
    except PennylaneNotConfiguredError as exc:
        assert "PENNYLANE_API_TOKEN" in str(exc)
    else:
        raise AssertionError("Expected PennylaneNotConfiguredError")

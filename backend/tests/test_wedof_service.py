from __future__ import annotations

from datetime import datetime, timezone

from edof_netz.services.wedof import (
    WedofNotConfiguredError,
    _attendee_raw_id,
    _float_value,
    _parse_datetime,
    _str_value,
    get_wedof_client,
)


def test_parse_datetime_handles_iso_string() -> None:
    assert _parse_datetime("2024-01-15T10:30:00Z") == datetime(
        2024, 1, 15, 10, 30, tzinfo=timezone.utc
    )


def test_parse_datetime_returns_none_for_invalid() -> None:
    assert _parse_datetime("not-a-date") is None
    assert _parse_datetime(None) is None


def test_parse_datetime_adds_utc_when_naive() -> None:
    dt = _parse_datetime("2024-01-15T10:30:00")
    assert dt == datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc)


def test_str_value_tries_keys_in_order() -> None:
    assert _str_value({"a": 1, "b": "two"}, "a", "b") == "1"
    assert _str_value({"b": "two"}, "a", "b") == "two"
    assert _str_value({}, "a") is None


def test_float_value_tries_keys_and_skips_invalid() -> None:
    assert _float_value({"a": "1.5", "b": "bad"}, "a", "b") == 1.5
    assert _float_value({"b": "bad"}, "a", "b") is None
    assert _float_value({}, "a") is None


def test_attendee_raw_id_from_nested_dict() -> None:
    raw = {"attendee": {"id": 12345, "email": "test@example.com"}}
    assert _attendee_raw_id(raw) == 12345.0


def test_attendee_raw_id_from_flat_key() -> None:
    assert _attendee_raw_id({"attendeeId": 99}) == 99.0
    assert _attendee_raw_id({"attendee_id": 42}) == 42.0


def test_attendee_raw_id_returns_none_when_missing() -> None:
    assert _attendee_raw_id({}) is None


def test_get_wedof_client_raises_when_key_missing(monkeypatch) -> None:
    monkeypatch.delenv("WEDOF_API_KEY", raising=False)
    try:
        get_wedof_client()
    except WedofNotConfiguredError as exc:
        assert "WEDOF_API_KEY" in str(exc)
    else:
        raise AssertionError("Expected WedofNotConfiguredError")

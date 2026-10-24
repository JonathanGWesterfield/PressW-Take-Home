"""Focused checks for compatibility parsing and byte-sensitive value mapping."""
import json
from decimal import Decimal

import pytest
from sqlalchemy.exc import DataError

from encore.app.crew import legacy
from encore.app.crew.models import CrewRecord


def test_raw_query_keeps_first_value_and_malformed_escape_visible():
    pairs = legacy._query_pairs(b"%70age=2&page=1&crew_id=%FF&plus=1%2B2+3")

    assert legacy._first(pairs, "page", "1") == "2"
    assert legacy._first(pairs, "crew_id", "") == "%FF"
    assert legacy._first(pairs, "plus", "") == "1+2 3"


def test_legacy_serializer_preserves_null_and_raw_detail_rules():
    record = CrewRecord(
        id=9,
        org_id=7,
        user_name=None,
        display_name=None,
        rate=None,
        is_lead="y",
        notes=None,
        preferences_raw="{broken",
    )

    listing = legacy._legacy_record(record, detail=False)
    detail = legacy._legacy_record(record, detail=True)

    assert list(listing) == ["crew_id", "crew_name", "display_name", "is_lead", "notes", "org", "rate"]
    assert listing == {
        "crew_id": 9,
        "crew_name": "",
        "display_name": None,
        "is_lead": "N",
        "notes": "",
        "org": 7,
        "rate": "",
    }
    assert detail["prefs"] == "{broken"


def test_legacy_serializer_rounds_stored_money_and_uppercase_lead_only():
    record = CrewRecord(9, 7, "marta", "Marta", Decimal("27.335"), "Y", "note", None)

    assert legacy._legacy_record(record, detail=False)["rate"] == "27.34"
    assert legacy._legacy_record(record, detail=False)["is_lead"] == "Y"


def test_legacy_database_errors_distinguish_range_and_malformed_text():
    assert "out of range" in legacy._legacy_database_error("9" * 5000)
    assert legacy._legacy_database_error("") == (
        'invalid input syntax for type integer: ""\n'
        "CONTEXT:  unnamed portal parameter $1 = ''"
    )
    assert legacy._legacy_database_error("\x00") == "PostgreSQL text fields cannot contain NUL (0x00) bytes"


def test_legacy_org_parser_rejects_python_only_forms_but_keeps_digit_errors():
    def request(value):
        return type("Request", (), {"scope": {"headers": [(b"x-org-id", value.encode("latin-1"))]}})()

    assert legacy._org_id(request("9_00071")) == (None, "missing org")
    assert legacy._org_id(request("-0")) == (None, "missing org")
    assert legacy._org_id(request(" 900071 ")) == (900071, None)
    assert legacy._org_id(request("³"))[1] == "invalid literal for int() with base 10: '³'"


def test_legacy_redirect_html_escapes_query_separators_without_changing_location():
    request = type(
        "Request",
        (),
        {"scope": {"headers": [(b"host", b"localhost:8091")], "query_string": b"a=1&b=2"}},
    )()

    response = legacy._redirect(request, "/callboard/crew/list")

    assert response.headers["location"] == "http://localhost:8091/callboard/crew/list?a=1&b=2"
    assert b"a=1&amp;b=2" in response.body


class _Request:
    method = "GET"
    scope = {
        "raw_path": b"/callboard/crew/show",
        "path": "/callboard/crew/show",
        "query_string": b"crew_id=bad",
        "headers": [(b"x-org-id", b"7")],
    }


class _ConversionFailureService:
    def get_for_org_raw_id(self, org_id, crew_id):
        raise DataError("SELECT", {"crew_id": crew_id}, ValueError("bad integer"))


class _OperationalFailureService:
    def get_for_org_raw_id(self, org_id, crew_id):
        raise RuntimeError("database unavailable")


def test_legacy_dispatch_maps_only_database_conversion_failures(monkeypatch):
    monkeypatch.setattr(legacy, "_service", _ConversionFailureService())

    response = legacy.dispatch(_Request())

    assert json.loads(response.body) == {
        "error": 'invalid input syntax for type integer: "bad"\n'
        "CONTEXT:  unnamed portal parameter $1 = '...'",
        "result": "fail",
    }


def test_legacy_dispatch_does_not_mask_operational_failures(monkeypatch):
    monkeypatch.setattr(legacy, "_service", _OperationalFailureService())

    with pytest.raises(RuntimeError, match="database unavailable"):
        legacy.dispatch(_Request())

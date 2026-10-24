"""Byte-compatible Callboard crew read wrappers.

This module is intentionally isolated from the modern v3 adapter.  Its loose
parsing, compact JSON, and database parser diagnostics are compatibility
requirements captured before the migration, not choices for new endpoints.
"""
from __future__ import annotations

import json
import re
from collections.abc import Iterable
from html import escape
from urllib.parse import unquote_to_bytes

from fastapi import Request
from fastapi.responses import Response
from sqlalchemy.exc import DataError

from .models import CrewRecord
from .service import CrewService


_LIST = "/callboard/crew/list"
_SHOW = "/callboard/crew/show"
_NOT_FOUND = (
    "404 Not Found: The requested URL was not found on the server. "
    "If you entered the URL manually please check your spelling and try again."
)
_METHOD_NOT_ALLOWED = "405 Method Not Allowed: The method is not allowed for the requested URL."
_INTEGER_LITERAL = re.compile(r"^[ \t\r\n]*([+-]?)([0-9]+)[ \t\r\n]*$")
_service = CrewService()


def _json(payload: dict[str, object]) -> Response:
    return Response(
        content=json.dumps(payload, ensure_ascii=True, separators=(",", ":")) + "\n",
        media_type="application/json",
    )


def _failure(error: str) -> Response:
    return _json({"error": error, "result": "fail"})


def _decode_component(value: bytes) -> str:
    """Decode ordinary form fields, retaining malformed bytes as Callboard did."""
    plus_as_space = value.replace(b"+", b" ")
    decoded = unquote_to_bytes(plus_as_space)
    try:
        return decoded.decode("utf-8")
    except UnicodeDecodeError:
        # Werkzeug kept these malformed escape sequences visible to the DB
        # parser rather than replacing them with U+FFFD.
        return plus_as_space.decode("latin-1")


def _query_pairs(raw_query: bytes) -> list[tuple[str, str]]:
    if not raw_query:
        return []
    pairs = []
    for part in raw_query.split(b"&"):
        key, separator, value = part.partition(b"=")
        pairs.append((_decode_component(key), _decode_component(value if separator else b"")))
    return pairs


def _first(pairs: Iterable[tuple[str, str]], name: str, default: str) -> str:
    for key, value in pairs:
        if key == name:
            return value
    return default


def _org_id(request: Request) -> tuple[int | None, str | None]:
    values = [
        value.decode("latin-1")
        for name, value in request.scope["headers"]
        if name.lower() == b"x-org-id"
    ]
    if len(values) != 1:
        return None, "missing org"
    value = values[0]
    if not value.strip().isdigit():
        return None, "missing org"
    try:
        parsed = int(value)
    except ValueError as exc:
        # Callboard only surfaced the odd Unicode-digit conversion error; its
        # normal malformed header path collapsed to "missing org".  Python's
        # large-integer guard is the other observed exception it returned.
        if str(exc).startswith("invalid literal") or str(exc).startswith("Exceeds the limit"):
            return None, str(exc)
        return None, "missing org"
    return parsed, None


def _legacy_record(record: CrewRecord, *, detail: bool) -> dict[str, object]:
    data: dict[str, object] = {
        "crew_id": record.id,
        "crew_name": record.user_name or "",
        "display_name": record.display_name,
        "is_lead": "Y" if record.is_lead == "Y" else "N",
        "notes": record.notes or "",
        "org": record.org_id,
    }
    if detail:
        data["prefs"] = record.preferences_raw or ""
    data["rate"] = format(record.rate, ".2f") if record.rate is not None else ""
    return data


def _legacy_database_error(raw_id: str) -> str:
    if "\x00" in raw_id:
        return "PostgreSQL text fields cannot contain NUL (0x00) bytes"
    match = _INTEGER_LITERAL.fullmatch(raw_id)
    if match is not None:
        sign, raw_digits = match.groups()
        digits = raw_digits.lstrip("0") or "0"
        maximum = "2147483648" if sign == "-" else "2147483647"
        if len(digits) > len(maximum) or (len(digits) == len(maximum) and digits > maximum):
            return (
                f'value "{raw_id}" is out of range for type integer\n'
                "CONTEXT:  unnamed portal parameter $1 = '...'"
            )
    context = "''" if raw_id == "" else "'...'"
    return (
        f'invalid input syntax for type integer: "{raw_id}"\n'
        f"CONTEXT:  unnamed portal parameter $1 = {context}"
    )


def _redirect(request: Request, target: str) -> Response:
    host = next(
        (value.decode("latin-1") for name, value in request.scope["headers"] if name.lower() == b"host"),
        "localhost",
    )
    location = f"http://{host}{target}"
    raw_query = request.scope["query_string"]
    if raw_query:
        location += "?" + raw_query.decode("latin-1")
    body = (
        "<!doctype html>\n<html lang=en>\n<title>Redirecting...</title>\n"
        "<h1>Redirecting...</h1>\n<p>You should be redirected automatically to the target URL: "
        f'<a href="{escape(location, quote=True)}">{escape(location, quote=True)}</a>. If not, click the link.\n'
    )
    return Response(body, status_code=308, media_type="text/html", headers={"location": location})


def _decoded_path(request: Request) -> str:
    raw_path = request.scope.get("raw_path", request.scope["path"].encode("utf-8"))
    try:
        return unquote_to_bytes(raw_path).decode("utf-8")
    except UnicodeDecodeError:
        return raw_path.decode("latin-1")


def dispatch(request: Request) -> Response | None:
    """Return a legacy response for crew candidates, else defer to FastAPI."""
    path = _decoded_path(request)
    if path in ("/callboard//crew/list", "/callboard//crew/show"):
        return _redirect(request, path.replace("//", "/", 1))
    candidate = path.lower()
    if not (candidate.startswith("/callboard/crew") or candidate.startswith("/callboard//crew")):
        return None
    if path not in (_LIST, _SHOW):
        return _failure(_NOT_FOUND)
    org_id, org_error = _org_id(request)
    if org_error is not None:
        return _failure(org_error)
    if request.method == "OPTIONS":
        return Response(
            status_code=200,
            media_type="text/html",
            headers={"allow": "GET, HEAD, OPTIONS"},
        )
    if request.method not in {"GET", "HEAD"}:
        return _failure(_METHOD_NOT_ALLOWED)
    pairs = _query_pairs(request.scope["query_string"])
    if path == _LIST:
        try:
            page = int(_first(pairs, "page", "1") or "1")
            per_page = int(_first(pairs, "per_page", "25") or "25")
        except ValueError as exc:
            return _failure(str(exc))
        if page <= 0:
            page = 1
        records = _service.list_for_org(org_id)
        selected = records if per_page == 0 else records[(page - 1) * per_page : page * per_page]
        return _json(
            {
                "data": {"crew": [_legacy_record(record, detail=False) for record in selected], "page": page, "total": len(records)},
                "result": "ok",
                "tg_flash": None,
            }
        )

    crew_id = _first(pairs, "crew_id", "")
    try:
        record = _service.get_for_org_raw_id(org_id, crew_id)
    except DataError:
        # Only conversion failures are part of the captured Callboard wire
        # contract. Connectivity and programming failures must remain visible
        # to normal service error handling.
        return _failure(_legacy_database_error(crew_id))
    if record is None:
        return _failure("not found")
    return _json({"data": _legacy_record(record, detail=True), "result": "ok", "tg_flash": None})

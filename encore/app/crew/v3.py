"""Strict, intentionally modern HTTP contract for read-only crew endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Request, Response, status
from pydantic import BaseModel

from .models import CrewRecord
from .service import CrewService


router = APIRouter(prefix="/v3", tags=["crew"])
_INT32_MAX = 2_147_483_647
_POSITIVE_DECIMAL_PATTERN = r"^[0-9]*[1-9][0-9]*$"
_ORG_PARAMETER = {
    "name": "X-Org-Id",
    "in": "header",
    "required": True,
    "description": "One positive ASCII decimal integer from 1 through 2147483647.",
    "schema": {"type": "string", "pattern": _POSITIVE_DECIMAL_PATTERN},
}


class CrewItem(BaseModel):
    id: int
    org_id: int
    user_name: str | None
    display_name: str | None
    rate: str | None
    is_lead: bool
    notes: str | None


class CrewDetail(CrewItem):
    preferences_raw: str | None


class CrewList(BaseModel):
    items: list[CrewItem]
    page: int
    page_size: int
    total: int


def get_crew_service() -> CrewService:
    return CrewService()


def _validation_error(field: str, reason: str) -> None:
    # FastAPI's standard HTTP error envelope is deliberate here.  Unlike the
    # legacy adapter, it never includes parser, driver, or SQL diagnostics.
    raise HTTPException(
        status_code=422,
        detail=f"{field}: {reason}",
    )


def _positive_ascii_int(value: str, field: str, maximum: int | None = None) -> int:
    if not value or not value.isascii() or not value.isdecimal():
        _validation_error(field, "must be a positive ASCII decimal integer")
    try:
        parsed = int(value)
    except ValueError:
        # Python itself declines integers with thousands of digits.  This is a
        # normal modern validation error, never a database parser leak.
        _validation_error(field, "must be a positive ASCII decimal integer")
    if parsed < 1:
        _validation_error(field, "must be a positive ASCII decimal integer")
    if maximum is not None and parsed > maximum:
        _validation_error(field, f"must be between 1 and {maximum}")
    return parsed


def _org_id(request: Request) -> int:
    values = [
        value.decode("latin-1")
        for name, value in request.scope["headers"]
        if name.lower() == b"x-org-id"
    ]
    if len(values) != 1:
        _validation_error("X-Org-Id", "must be supplied exactly once")
    return _positive_ascii_int(values[0], "X-Org-Id", _INT32_MAX)


def _query(request: Request, allowed: set[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for key, value in request.query_params.multi_items():
        if key not in allowed:
            _validation_error("query parameter", f"{key!r} is not supported")
        if key in values:
            _validation_error("query parameter", f"{key!r} must not be repeated")
        values[key] = value
    return values


def _item(record: CrewRecord) -> CrewItem:
    # Postgres NUMERIC arrives as Decimal. Formatting it as Decimal preserves
    # the stored two-place money value without a binary float round trip.
    rate = format(record.rate, ".2f") if record.rate is not None else None
    return CrewItem(
        id=record.id,
        org_id=record.org_id,
        user_name=record.user_name,
        display_name=record.display_name,
        rate=rate,
        is_lead=record.is_lead == "Y",
        notes=record.notes,
    )


def _detail(record: CrewRecord) -> CrewDetail:
    return CrewDetail(**_item(record).model_dump(), preferences_raw=record.preferences_raw)


@router.get(
    "/crew",
    response_model=CrewList,
    responses={422: {"description": "Strict header or query validation failed."}},
    openapi_extra={
        "parameters": [
            _ORG_PARAMETER,
            {
                "name": "page",
                "in": "query",
                "required": False,
                "description": "Positive ASCII decimal page number. Defaults to 1; no int32 ceiling.",
                "schema": {"type": "string", "pattern": _POSITIVE_DECIMAL_PATTERN, "default": "1"},
            },
            {
                "name": "page_size",
                "in": "query",
                "required": False,
                "description": "Positive ASCII decimal page size from 1 through 100. Defaults to 25.",
                "schema": {"type": "string", "pattern": _POSITIVE_DECIMAL_PATTERN, "default": "25"},
            },
        ]
    },
)
def list_crew(
    request: Request,
    service: Annotated[CrewService, Depends(get_crew_service)],
) -> CrewList:
    org_id = _org_id(request)
    query = _query(request, {"page", "page_size"})
    page = _positive_ascii_int(query.get("page", "1"), "page")
    page_size = _positive_ascii_int(query.get("page_size", "25"), "page_size")
    if page_size > 100:
        _validation_error("page_size", "must be between 1 and 100")

    records = service.list_for_org(org_id)
    start = (page - 1) * page_size
    return CrewList(
        items=[_item(record) for record in records[start : start + page_size]],
        page=page,
        page_size=page_size,
        total=len(records),
    )


@router.get(
    "/crew/{crew_id}",
    response_model=CrewDetail,
    responses={
        404: {"description": "No crew record is visible in the requested organization."},
        422: {"description": "Strict header, path, or query validation failed."},
    },
    openapi_extra={
        "parameters": [
            _ORG_PARAMETER,
        ]
    },
)
def get_crew(
    crew_id: Annotated[
        str,
        Path(
            description="Positive ASCII decimal crew identifier from 1 through 2147483647.",
            pattern=_POSITIVE_DECIMAL_PATTERN,
        ),
    ],
    request: Request,
    service: Annotated[CrewService, Depends(get_crew_service)],
) -> CrewDetail:
    org_id = _org_id(request)
    _query(request, set())
    parsed_crew_id = _positive_ascii_int(crew_id, "crew_id", _INT32_MAX)
    record = service.get_for_org(org_id, parsed_crew_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crew not found")
    return _detail(record)


def _trailing_slash_not_found() -> Response:
    """Make v3 trailing slashes 404 without changing legacy/global routing."""
    return Response(status_code=status.HTTP_404_NOT_FOUND, media_type="application/json", content='{"detail":"Not Found"}')


# FastAPI otherwise redirects these paths before the normal routes can emit the
# documented 404.  Cover common methods so a trailing slash cannot become an
# accidental method-specific public endpoint.
@router.api_route(
    "/crew/",
    methods=["GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE", "TRACE"],
    include_in_schema=False,
)
@router.api_route(
    "/crew/{crew_id}/",
    methods=["GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE", "TRACE"],
    include_in_schema=False,
)
def trailing_slash_not_found() -> Response:
    return _trailing_slash_not_found()

"""Typed values shared by the crew repository and its HTTP adapters."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class CrewRecord:
    """The explicitly approved read-only subset of ``tg_crew``.

    Passwords, organization labels, and creation timestamps deliberately do not
    cross this boundary.
    """

    id: int
    org_id: int
    user_name: str | None
    display_name: str | None
    rate: Decimal | None
    is_lead: str | None
    notes: str | None
    preferences_raw: str | None

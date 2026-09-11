"""Gopher State One Call, as a typed hold with two derived dates.

A locate is the one hold on this board whose dates are *not* the owner's judgement: Minn.
Stat. 216D.04 subd. 1a fixes them. The excavator gives notice, the ticket arms 48 hours
later excluding weekends and legal holidays, and it is good for 14 calendar days — six
months where the operators and the excavator have a written refresh agreement.

So this module derives two dates and nothing else. It does not guess when the digging
starts, it does not pick a notice date, and with no authored ``start`` it derives nothing
at all and says so. Decision #69 as this review loosened it: dates are derived only from
authored inputs, and a missing input yields "needs confirmation", never a default.

Legal holidays are a house fact (``[calendar]`` in ``tasks.toml``), not an engine constant:
the statute says "legal holidays" and which ones those are is a jurisdiction's answer.
Without an authored list the arming date counts weekends only, and the derived sentence
says exactly that so nobody reads it as the statutory answer.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

#: Minn. Stat. 216D.04 subd. 1a: notice at least 48 hours, excluding weekends and holidays.
ARMING_HOURS = 48
#: Minn. Stat. 216D.04 subd. 3: the ticket's life, in calendar days.
TICKET_DAYS = 14
#: With a written refresh agreement under subd. 3, measured in calendar days.
REFRESH_DAYS = 183
#: How many days ahead the board starts warning that a ticket is running out.
EXPIRY_WARNING_DAYS = 3


def parse_date(text: Any) -> date | None:
    """``"2027-05-03"`` -> a date. Anything else is prose and derives nothing."""
    if isinstance(text, date):
        return text
    try:
        return date.fromisoformat(str(text).strip()[:10])
    except (ValueError, TypeError):
        return None


def add_working_days(start: date, days: int, holidays: frozenset[date] = frozenset()
                     ) -> date:
    """``start`` plus ``days`` days that are neither a weekend nor a named holiday."""
    seen, cursor = 0, start
    while seen < days:
        cursor += timedelta(days=1)
        if cursor.weekday() < 5 and cursor not in holidays:
            seen += 1
    return cursor


def locate_dates(hold: Any, holidays: frozenset[date] = frozenset()
                 ) -> tuple[str | None, str | None, str]:
    """``(armed, expires, the sentence that says how)`` for one hold.

    Empty on any hold that is not ``kind = "locate"``. A locate with no ``start`` derives
    no dates and returns the sentence asking for one — that is the "needs confirmation"
    state, and it is a fact about the ticket, not a default for it.
    """
    if str(getattr(hold, "kind", "") or "") != "locate":
        return None, None, ""
    start = parse_date(getattr(hold, "start", None))
    if start is None:
        return None, None, ("locate ticket: no notice date authored, so nothing is derived "
                            "— enter the date the ticket was called in")
    armed = add_working_days(start, ARMING_HOURS // 24, holidays)
    life = REFRESH_DAYS if getattr(hold, "refresh_agreement", False) else TICKET_DAYS
    expires = start + timedelta(days=life)
    basis = ("a written refresh agreement" if life == REFRESH_DAYS
             else f"{TICKET_DAYS} calendar days")
    counted = ("weekends and the house calendar's holidays" if holidays
               else "weekends only — no [calendar] holidays are authored")
    return (armed.isoformat(), expires.isoformat(),
            f"Minn. Stat. 216D.04: notice {start.isoformat()}, arms after {ARMING_HOURS}h "
            f"excluding {counted}, expires on {basis}")


def locate_state(hold: Any, today: date | None = None) -> str:
    """``""`` | ``"pending"`` | ``"armed"`` | ``"expiring"`` | ``"expired"``.

    A locate blocks its visit before it arms *and* after it expires, which is the one hold
    on this board that can close again on its own.
    """
    armed, expires, _ = locate_dates(hold)
    if armed is None:
        return "needs_confirmation" if str(getattr(hold, "kind", "")) == "locate" else ""
    now = today or date.today()
    if now < date.fromisoformat(armed):
        return "pending"
    if expires is not None:
        end = date.fromisoformat(expires)
        if now > end:
            return "expired"
        if (end - now).days <= EXPIRY_WARNING_DAYS:
            return "expiring"
    return "armed"

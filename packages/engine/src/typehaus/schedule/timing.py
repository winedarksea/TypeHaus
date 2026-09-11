"""Dates, derived only from authored inputs — and "needs confirmation" where there are none.

Decision #69 as this review loosened it: **readiness is derived; dates are derived only
from authored inputs, and a missing input yields "needs confirmation", never a default.**
Nothing in this module ships a duration, a lead time or a productivity rate. A visit with no
``duration_days`` produces no suggested date and blocks nothing; a material with no
``lead_days`` says "lead time unknown" and the board asks for it.

Four date kinds, and only one of them is the engine's:

``suggested``  the earliest feasible date from dependencies, durations, cures and leads
``planned``    the owner's intent, not yet confirmed with the sub
``booked``     confirmed with the sub: a date, a window, who confirmed it and when
``actual``     what happened, per visit and per checkpoint

**A booking is never moved.** A predecessor that slips past one marks it *threatened*, with
the slack in days, and leaves the date where the owner and the sub agreed it would be. An
engine that silently rebooked a concrete truck would be worse than one that computed
nothing.

A leaf like ``engineering/`` and ``routing/``: it reads visits, inspections and the house
calendar, and imports nothing from ``checks``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

from typehaus.schedule.graph import INSPECTION_PREFIX
from typehaus.schedule.locates import parse_date

#: What a missing authored input produces. Not a date, and deliberately not a blank either:
#: a board that shows nothing beside a visit reads as "no constraint", and the true sentence
#: is "nobody has said yet".
NEEDS_CONFIRMATION = "needs confirmation"

#: How far ahead the board asks for a lead time it does not have.
LEAD_TIME_PROMPT_DAYS = 30


@dataclass(frozen=True)
class Calendar:
    """Which days are worked. The house's, never the engine's."""

    workdays: frozenset[int] = frozenset({0, 1, 2, 3, 4})
    holidays: frozenset[date] = frozenset()

    @classmethod
    def of(cls, tasks_state: Any) -> Calendar:
        authored = getattr(tasks_state, "calendar", None)
        if authored is None:
            return cls()
        days = frozenset(int(d) for d in authored.workdays)
        holidays = frozenset(d for d in (parse_date(x) for x in authored.holidays)
                             if d is not None)
        return cls(workdays=days or frozenset({0, 1, 2, 3, 4}), holidays=holidays)

    def is_workday(self, day: date) -> bool:
        return day.weekday() in self.workdays and day not in self.holidays

    def next_workday(self, day: date) -> date:
        while not self.is_workday(day):
            day += timedelta(days=1)
        return day

    def add_workdays(self, start: date, days: int) -> date:
        """``start`` is day one. A one-day visit starting Friday finishes Friday."""
        day = self.next_workday(start)
        for _ in range(max(days - 1, 0)):
            day = self.next_workday(day + timedelta(days=1))
        return day

    def minus_workdays(self, end: date, days: int) -> date:
        day = end
        for _ in range(max(days, 0)):
            day -= timedelta(days=1)
            while not self.is_workday(day):
                day -= timedelta(days=1)
        return day


@dataclass(frozen=True)
class VisitDates:
    """Everything this module can say about one visit's calendar."""

    slug: str
    suggested_start: str | None = None
    suggested_finish: str | None = None
    planned: str | None = None
    booked: str | None = None
    #: Set when a predecessor's suggested finish falls after the booked date.
    threatened_by_days: int | None = None
    #: Why there is no suggested date, where there is none.
    why: str = ""
    materials: tuple[dict[str, Any], ...] = ()

    @property
    def needs_confirmation(self) -> bool:
        return self.suggested_start is None

    def as_dict(self) -> dict[str, Any]:
        return {"slug": self.slug, "suggested_start": self.suggested_start,
                "suggested_finish": self.suggested_finish, "planned": self.planned,
                "booked": self.booked, "threatened_by_days": self.threatened_by_days,
                "why": self.why or (NEEDS_CONFIRMATION if self.needs_confirmation else ""),
                "materials": [dict(m) for m in self.materials]}


@dataclass
class _Solver:
    calendar: Calendar
    by_slug: dict[str, Any] = field(default_factory=dict)
    finish: dict[str, date] = field(default_factory=dict)
    reason: dict[str, str] = field(default_factory=dict)


def _cure_days(visit: Any) -> int:
    return sum(int(p.get("cure_days") or 0) for p in visit.checkpoints)


def _anchor(visit: Any) -> date | None:
    """A date this visit is pinned to regardless of its predecessors."""
    booked = (visit.booked or {}).get("date") if isinstance(visit.booked, dict) else None
    return parse_date(booked) or parse_date(visit.planned) or parse_date(visit.scheduled)


def visit_dates(board: Any, tasks_state: Any, today: date | None = None
                ) -> dict[str, VisitDates]:
    """Suggested, planned and booked dates for every visit on the board.

    The suggested date is a forward pass over the dependency graph: a visit starts the next
    working day after the last of its predecessors finishes, plus any cure the predecessor's
    checkpoints declare. A predecessor with no duration propagates "needs confirmation"
    forward rather than a guess, which is why one unquoted sub greys a whole branch — that
    is the honest picture and the prompt to go and get the number.
    """
    calendar = Calendar.of(tasks_state)
    start_of = {visit.slug: _anchor(visit) for visit in board.visits}
    order = _topological(board)
    finish: dict[str, date] = {}
    start: dict[str, date] = {}
    why: dict[str, str] = {}

    for slug in order:
        visit = board.visit(slug)
        if visit is None:
            continue
        earliest: date | None = start_of[slug] or (today or date.today())
        blocked = ""
        for dependency in visit.depends_on:
            if dependency.startswith(INSPECTION_PREFIX):
                continue
            base = dependency.split("#", 1)[0]
            done = finish.get(base)
            if done is None:
                blocked = blocked or (
                    f"{base} has no duration authored, so nothing after it can be dated")
                continue
            after = calendar.next_workday(done + timedelta(days=1))
            earliest = max(earliest, after) if earliest else after
        duration = _duration(tasks_state, slug)
        if start_of[slug] is not None:
            # An authored date wins over the forward pass: the owner and the sub agreed it.
            earliest = start_of[slug]
        elif blocked:
            why[slug] = blocked
            continue
        if duration is None or earliest is None:
            why[slug] = why.get(slug) or (
                f"no duration_days authored for {slug}")
            continue
        start[slug] = calendar.next_workday(earliest)
        finish[slug] = calendar.add_workdays(start[slug], duration) + timedelta(
            days=_cure_days(visit))

    out: dict[str, VisitDates] = {}
    for visit in board.visits:
        booked = (visit.booked or {}).get("date") if isinstance(visit.booked, dict) else None
        threatened = _threat(visit, board, finish, parse_date(booked))
        out[visit.slug] = VisitDates(
            slug=visit.slug,
            suggested_start=start[visit.slug].isoformat() if visit.slug in start else None,
            suggested_finish=(finish[visit.slug].isoformat()
                              if visit.slug in finish else None),
            planned=visit.planned, booked=booked, threatened_by_days=threatened,
            why=why.get(visit.slug, ""),
            materials=_materials(visit, start.get(visit.slug), calendar, today))
    return out


def _duration(tasks_state: Any, slug: str) -> int | None:
    entry = getattr(getattr(tasks_state, "visits", None), "entries", {}).get(slug)
    return getattr(entry, "duration_days", None) if entry is not None else None


def _threat(visit: Any, board: Any, finish: dict[str, date],
            booked: date | None) -> int | None:
    """Days by which a predecessor overruns this booking. ``None`` when it does not."""
    if booked is None:
        return None
    worst = 0
    for dependency in visit.depends_on:
        base = dependency.split("#", 1)[0]
        done = finish.get(base)
        if done is not None and done >= booked:
            worst = max(worst, (done - booked).days + 1)
    return worst or None


def _materials(visit: Any, start: date | None, calendar: Calendar,
               today: date | None) -> tuple[dict[str, Any], ...]:
    """``order_by = suggested start - lead_days``, and a prompt where the lead is unknown."""
    out: list[dict[str, Any]] = []
    for item in getattr(visit, "materials", ()) or ():
        row = dict(item)
        lead = row.get("lead_days")
        if lead is None:
            row["order_by"] = None
            row["why"] = "lead time unknown — ask the supplier"
            row["ask_now"] = bool(
                start is not None
                and (start - (today or date.today())).days <= LEAD_TIME_PROMPT_DAYS)
        elif start is not None and not row.get("order_by"):
            row["order_by"] = calendar.minus_workdays(start, int(lead)).isoformat()
        # An expected delivery is a promise. Only `received` is a fact.
        row["on_site"] = bool(row.get("received"))
        out.append(row)
    return tuple(out)


def latest_request(booked: str | None, lead_days: int | None,
                   calendar: Calendar) -> str | None:
    """The last working day an inspection can be called in for a booked appointment."""
    when = parse_date(booked)
    if when is None or lead_days is None:
        return None
    return calendar.minus_workdays(when, int(lead_days)).isoformat()


def inspection_dates(inspections: Any, authorities: Any, tasks_state: Any,
                     today: date | None = None) -> dict[str, dict[str, Any]]:
    """Per inspection: the earliest it can happen, and the last day to call it in.

    These two used to live in the UI, where they counted weekends and could not see the
    house's ``[calendar]``. A holiday the owner authored is a working day to a client that
    does not know about it, which makes the one date on that screen the one date that is
    wrong. Both are derived from the authority's own published ``lead_days`` and nothing
    else: an authority that has not stated one gets ``None`` and the board says so.
    """
    calendar = Calendar.of(tasks_state)
    now = today or date.today()
    out: dict[str, dict[str, Any]] = {}
    for record in inspections:
        authority = (authorities or {}).get(record.authority)
        lead = getattr(authority, "lead_days", None)
        booked = (record.entry or {}).get("scheduled") if record.entry else None
        out[record.id] = {
            "lead_days": lead,
            "earliest_call": (calendar.add_workdays(now, int(lead) + 1).isoformat()
                              if lead is not None else None),
            "latest_request": latest_request(booked, lead, calendar),
            "why": ("" if lead is not None else
                    "no lead time published — Minn. R. 1300.0210 subp. 4 obliges the "
                    "authority to state it at permit issuance; ask and write it in"),
        }
    return out


def _topological(board: Any) -> tuple[str, ...]:
    """Visits in dependency order; a node on a cycle comes last, never dropped."""
    edges = {visit.slug: tuple(d.split("#", 1)[0] for d in visit.depends_on
                               if not d.startswith(INSPECTION_PREFIX))
             for visit in board.visits}
    seen: set[str] = set()
    order: list[str] = []
    for start in sorted(edges):
        stack = [(start, iter(edges.get(start, ())))]
        on_path = {start}
        while stack:
            node, children = stack[-1]
            nxt = next(children, None)
            if nxt is None:
                stack.pop()
                on_path.discard(node)
                if node not in seen:
                    seen.add(node)
                    order.append(node)
                continue
            if nxt in seen or nxt in on_path or nxt not in edges:
                continue
            on_path.add(nxt)
            stack.append((nxt, iter(edges.get(nxt, ()))))
    return tuple(order)

"""Turning authored ``[visits]`` and derived work packages into one list of arrivals.

Split from :mod:`typehaus.schedule.readiness`, which now does one thing: derive readiness
from a list of visits. This module decides *what the visits are*, and that is three
different sentences.

An **implicit** visit is the whole package, for a house that has authored no split. It is
the only kind that still carries an inspection's ``gates`` (minus the circular ones — see
:mod:`typehaus.schedule.graph`), because a gate names a trade and a trade is only a
schedulable thing when nobody has split it.

An **authored** visit gets exactly its authored ``depends_on``. Where it authors none it
falls back to the *package's* predecessors, so splitting a package does not cut its
arrivals loose; it never inherits a trade-wide inspection gate.

A **standalone** visit (``site/<label>``) draws from no package at all: a locate, a
side-permit, a survey, a delivery, the punch list. Real arrivals with real holds, and the
board was blind to every one of them.
"""

from __future__ import annotations

from typing import Any

from typehaus.schedule.graph import implied_gates
from typehaus.schedule.milestones import MILESTONE_OF_TRADE
from typehaus.schedule.model import Constraint, Visit
from typehaus.takeoff.visit_state import VisitEntry, package_of

#: Set once per :func:`~typehaus.schedule.readiness.make_ready` call. ``WorkItem`` carries
#: its derived GlobalId but not the project uuid it came from, and threading a parameter
#: through for one value would put the project's identity in five signatures that have no
#: other use for it.
PROJECT_UUID: dict[str, Any] = {"value": None}


def _matches(tag: str, patterns: tuple[str, ...]) -> bool:
    """A tag against the visit's globs. No patterns means the whole package."""
    from fnmatch import fnmatch

    return not patterns or any(fnmatch(tag, pattern) for pattern in patterns)


def holds_of(entry: Any) -> tuple[Constraint, ...]:
    """An authored hold, carried across with everything that makes it actionable."""
    from typehaus.schedule.locates import locate_dates, locate_state

    out: list[Constraint] = []
    for hold in entry.constraints:
        armed, expires, derived = locate_dates(hold)
        cleared = hold.cleared
        if hold.kind == "locate":
            # A ticket is its own clearance and it closes again on its own: a locate is met
            # while it is live and unmet before it arms and after it lapses, whatever date
            # somebody ticked into `cleared`.
            state = locate_state(hold)
            cleared = armed if state in ("armed", "expiring") else None
            derived = f"{derived} — {state}" if derived else state
        out.append(Constraint(
            "authored", None, hold.label, cleared, severity=hold.severity,
            owner=hold.owner, next_action=hold.next_action, follow_up=hold.follow_up,
            ticket_kind=hold.kind, ticket=hold.ticket, ticket_start=hold.start,
            refresh_agreement=hold.refresh_agreement,
            armed=armed, expires=expires, derived=derived))
    return tuple(out)


def _unpaid(rows: tuple[tuple[str, str], ...], costs_entries: Any) -> bool:
    entries = getattr(costs_entries, "entries", {}) or {}
    for section, key in rows:
        entry = entries.get(section, {}).get(key)
        if entry is not None and getattr(entry, "actual_cost", None) is not None \
                and not getattr(entry, "paid", False):
            return True
    return False


def _guid(slug: str) -> str:
    from typehaus.model.ids import derive_guid

    return derive_guid(PROJECT_UUID["value"], slug)


def visit_from(item: Any, slug: str, entry: VisitEntry, depends_on: tuple[str, ...], *,
               implicit: bool, costs_entries: Any) -> Visit:
    rows = tuple(row for row in item.rows
                 if not entry.rows or f"{row[0]}:{row[1]}" in entry.rows)
    tags = tuple(tag for tag in item.element_tags if _matches(tag, entry.element_tags))
    status = entry.derived_status
    # A holdback is only *open* once the owner has verified the work and some row on it is
    # billed but unpaid. Before that there is nothing to hold back.
    holdback = bool(status == "verified" and _unpaid(rows, costs_entries))
    return Visit(
        slug=slug, id=_guid(slug), package=package_of(slug),
        label=entry.label or item.title, trade=item.trade, storey=item.storey,
        milestone=entry.milestone or MILESTONE_OF_TRADE.get(item.trade, ""),
        status=status, scheduled=entry.scheduled, assignee=entry.assignee,
        contact=entry.contact, note=entry.note, depends_on=tuple(depends_on),
        rows=rows, element_tags=tags, constraints=holds_of(entry),
        checked=tuple(entry.checked), estimate_fmt=item.estimate.fmt(),
        holdback_open=holdback, implicit=implicit,
        blocks_successors=entry.blocks_successors, shared_rows=entry.shared_rows,
        checkpoints=tuple(point.as_dict() for point in entry.checkpoints),
        exceptions=tuple(x.as_dict() for x in entry.exceptions),
        skipped=tuple(x.as_dict() for x in entry.skipped),
        log=tuple(x.as_dict() for x in entry.log), updated=entry.updated,
        planned=entry.planned, booked=entry.booked.as_dict() if entry.booked else None,
        duration_days=entry.duration_days, contractor=entry.contractor,
        materials=tuple(m.as_dict() for m in entry.materials))


def standalone_visit(slug: str, entry: VisitEntry) -> Visit:
    """``site/<label>``: no package, no BOM rows, no element tags — and still an arrival."""
    trade = entry.trade or ""
    return Visit(
        slug=slug, id=_guid(slug), package=slug,
        label=entry.label or slug.split("/", 1)[-1].replace("-", " ").capitalize(),
        trade=trade, storey=entry.storey or "building",
        milestone=entry.milestone or MILESTONE_OF_TRADE.get(trade, "preconstruction"),
        status=entry.derived_status, scheduled=entry.scheduled, assignee=entry.assignee,
        contact=entry.contact, note=entry.note, depends_on=tuple(entry.depends_on),
        constraints=holds_of(entry), checked=tuple(entry.checked),
        implicit=False, standalone=True, blocks_successors=entry.blocks_successors,
        shared_rows=entry.shared_rows,
        checkpoints=tuple(point.as_dict() for point in entry.checkpoints),
        exceptions=tuple(x.as_dict() for x in entry.exceptions),
        skipped=tuple(x.as_dict() for x in entry.skipped),
        log=tuple(x.as_dict() for x in entry.log), updated=entry.updated,
        planned=entry.planned, booked=entry.booked.as_dict() if entry.booked else None,
        duration_days=entry.duration_days, contractor=entry.contractor,
        materials=tuple(m.as_dict() for m in entry.materials))


def build_visits(work_items: Any, visits_state: Any, specs: tuple[Any, ...],
                 costs_entries: Any = None,
                 package_status: Any = None) -> tuple[Visit, ...]:
    """One :class:`Visit` per authored visit, one per unsplit package, plus the standalones.

    The implicit visit is what makes a house that has authored nothing still get a complete
    board: its slug **is** the package slug, and its predecessors are the package's own plus
    every inspection gate that :func:`~typehaus.schedule.graph.implied_gates` is willing to
    stand behind.

    **One status ladder.** That implicit visit takes its status from the package's
    ``[entries]`` row. There were two ladders before — a package could be ``done`` in
    ``[entries]`` while the board built its visit from a blank entry and showed ``todo`` —
    and two ladders that never meet is the same bug as no ladder at all.
    """
    statuses = dict(package_status or {})
    out: list[Visit] = []
    for item in work_items:
        authored = visits_state.for_package(item.slug) if visits_state is not None else {}
        if not authored:
            depends = tuple(item.depends_on) + implied_gates(item.trade, specs)
            out.append(visit_from(item, item.slug,
                                  VisitEntry(status=statuses.get(item.slug, "todo")),
                                  depends, implicit=True, costs_entries=costs_entries))
            continue
        for slug in sorted(authored):
            entry = authored[slug]
            out.append(visit_from(item, slug, entry,
                                  tuple(entry.depends_on) or tuple(item.depends_on),
                                  implicit=False, costs_entries=costs_entries))
    for slug, entry in sorted((visits_state.standalone if visits_state is not None
                               else {}).items()):
        out.append(standalone_visit(slug, entry))
    return tuple(out)


def mark_handoff_drift(visits: tuple[Visit, ...], model: Any) -> tuple[Visit, ...]:
    """A tick that names nothing, and a handoff set that grew under existing ticks.

    Neither is resolved here. A rename must not silently delete the owner's evidence that
    they walked something, and a new item must not silently inherit a tick from the old
    set — so the ticks are kept, the visit says ``needs re-walk``, and the orphans are
    listed for a person to look at.
    """
    from dataclasses import replace

    from typehaus.schedule.handoff import handoff_items

    if model is None:
        return visits
    out: list[Visit] = []
    for visit in visits:
        ids = {item.id for item in handoff_items(model, visit)}
        ticked = set(visit.checked) | {x["id"] for x in visit.skipped}
        orphans = tuple(sorted(ticked - ids))
        untouched = ids - ticked
        out.append(replace(visit, orphan_ticks=orphans,
                           needs_rewalk=bool(ticked and (orphans or untouched))))
    return tuple(out)

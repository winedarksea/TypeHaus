"""The states a house passes through, as contiguous slices of the trade order.

A milestone is the unit an owner-builder actually thinks in — "I need to be weathertight
before November" — and it is the only grouping on the board coarse enough to answer "where
am I". It is engine-generic: the slices are over ``emit.trades.CONSTRUCTION_SEQUENCE``, so
a jurisdiction contributes its inspections and nothing else.

Deliberately no dates and no order beyond the trade order that already exists. A milestone
is *done* when every visit in it is done, not when a date passes.

``preconstruction`` and ``complete`` own no trades either, and own only standalone visits:
permits, locates, utility coordination, deliveries, the final survey, the punch list. A
visit authored as ``site/<label>`` names its own milestone and lands in one of them.

``insulated`` owns no trades, and that is not an oversight. Insulation and air sealing are
billed inside the wall, roof and floor assemblies — the takeoff has no "insulation" trade
and inventing one to fill this row would put a trade in ``TRADES`` that no BOM row maps to.
What the milestone does own is the three inspections that decide whether the house may be
closed up, which is the whole reason it is a milestone rather than a step.
"""

from __future__ import annotations

from typing import Any

from typehaus.emit.trades import CONSTRUCTION_SEQUENCE
from typehaus.schedule.model import Milestone

#: ``(id, label, trades)`` in build order. The trade tuples partition
#: ``CONSTRUCTION_SEQUENCE`` exactly — ``_validate`` below refuses anything else, so a new
#: trade cannot be added upstream without somebody deciding where in the build it lands.
MILESTONE_SPECS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("preconstruction", "Preconstruction", ()),
    ("foundation", "Foundation", ("earth", "concrete", "drainage")),
    ("weathertight", "Weathertight", ("framing", "floors", "roof", "walls", "openings")),
    ("rough_ins", "Rough-ins", ("plumbing", "electrical", "mechanical")),
    ("insulated", "Insulated and closed up", ()),
    ("final", "Finishes", ("stairs", "furniture")),
    ("complete", "Complete", ()),
)

MILESTONE_IDS: tuple[str, ...] = tuple(spec[0] for spec in MILESTONE_SPECS)

#: trade -> milestone id. The lookup every other module in the package uses.
MILESTONE_OF_TRADE: dict[str, str] = {
    trade: milestone_id for milestone_id, _label, trades in MILESTONE_SPECS
    for trade in trades
}

LABELS: dict[str, str] = {spec[0]: spec[1] for spec in MILESTONE_SPECS}


def _validate() -> None:
    """Import-time guard: the slices partition the trade order, contiguously and in order."""
    flattened = [trade for _id, _label, trades in MILESTONE_SPECS for trade in trades]
    if flattened != list(CONSTRUCTION_SEQUENCE):
        raise ValueError(
            "MILESTONE_SPECS must partition CONSTRUCTION_SEQUENCE into contiguous slices, "
            f"in order; got {flattened} against {list(CONSTRUCTION_SEQUENCE)}")


_validate()


def milestone_table(tasks_state: Any = None) -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    """The milestone rows, with a house's ``[milestones]`` override folded in.

    A house may reorder, relabel or add rows; it may not take a trade's home away, so the
    trade tuples stay the engine's. An id the engine does not know gets an empty trade tuple
    and holds only the visits that name it — which is exactly what a house adding
    "landscaping" after ``complete`` wants.
    """
    authored = tuple(getattr(tasks_state, "milestones", ()) or ())
    if not authored:
        return MILESTONE_SPECS
    trades = {name: trade_tuple for name, _label, trade_tuple in MILESTONE_SPECS}
    rows = tuple((name, label, trades.get(name, ())) for name, label in authored)
    missing = [name for name in trades if name not in {row[0] for row in rows}]
    if missing:
        raise ValueError(f"[milestones] drops {missing}, which own trades; a house may "
                         "reorder and relabel the rows and add to them, not remove one")
    return rows


def milestone_of_inspection(spec: Any, by_id: dict[str, Any]) -> str:
    """Where an inspection sits, declared first and inherited only as a fallback.

    ``InspectionSpec.milestone`` is authoritative because no rule over ``after`` and
    ``gates`` can separate the slab inspection (foundation, gates ``floors``) from the
    braced-wall one (weathertight, gates ``walls``). An inspection that declares none —
    a house's own ``[[extra]]``, usually — inherits the latest milestone among its
    predecessors, which is right far more often than the first milestone would be.
    """
    declared = str(getattr(spec, "milestone", "") or "")
    if declared:
        if declared not in LABELS:
            raise ValueError(f"inspection {spec.id!r} names unknown milestone "
                             f"{declared!r}; known: {list(MILESTONE_IDS)}")
        return declared
    rank = {name: i for i, name in enumerate(MILESTONE_IDS)}
    inherited = [milestone_of_inspection(by_id[after], by_id)
                 for after in getattr(spec, "after", ()) if after in by_id]
    return max(inherited, key=rank.__getitem__) if inherited else MILESTONE_IDS[0]


def build_milestones(visits: Any, inspections: Any,
                     specs: tuple[tuple[str, str, tuple[str, ...]], ...] | None = None
                     ) -> tuple[Milestone, ...]:
    """Fill the rows with the visits and inspections that landed in each.

    ``state`` is derived from the visits alone: ``done`` when every visit in the milestone
    is done or verified, ``in_progress`` when any has moved off ``todo``. An empty
    milestone is ``not_started`` and stays there — claiming ``done`` for a row with nothing
    in it would mark a house weathertight because nobody had authored any walls.
    """
    table = specs or MILESTONE_SPECS
    ids = tuple(row[0] for row in table)
    default = ids[0]
    by_milestone_visits: dict[str, list[str]] = {name: [] for name in ids}
    by_milestone_inspections: dict[str, list[str]] = {name: [] for name in ids}
    statuses: dict[str, list[str]] = {name: [] for name in ids}
    resolved: dict[str, list[bool]] = {name: [] for name in ids}
    for visit in visits:
        name = visit.milestone or MILESTONE_OF_TRADE.get(visit.trade, default)
        by_milestone_visits.setdefault(name, []).append(visit.slug)
        statuses.setdefault(name, []).append(visit.status)
    for record in inspections:
        name = getattr(record, "milestone", "") or default
        by_milestone_inspections.setdefault(name, []).append(record.id)
        # An inspection that does not apply here is not a reason a milestone stays open,
        # and one that is merely waived by the AHJ is not either — both are resolved.
        applies = getattr(getattr(record, "applicability", None), "applies", True)
        if applies is not False:
            resolved.setdefault(name, []).append(bool(record.resolved))

    out: list[Milestone] = []
    for name, label, trades in table:
        seen = statuses[name]
        # A milestone completes only when its visits are settled **and** every applicable
        # inspection inside it is resolved. Weathertight with an unpassed braced-wall
        # inspection is not weathertight.
        if seen and all(status in ("done", "verified") for status in seen) \
                and all(resolved.get(name, ())):
            state = "done"
        elif any(status != "todo" for status in seen):
            state = "in_progress"
        else:
            state = "not_started"
        out.append(Milestone(id=name, label=label, trades=trades,
                             visits=tuple(by_milestone_visits[name]),
                             inspections=tuple(by_milestone_inspections.get(name, ())),
                             state=state))
    return tuple(out)


def current_milestone(milestones: tuple[Milestone, ...]) -> str:
    """The one to expand on the board: the first not-done row that holds anything.

    An *empty* row is skipped rather than reported. ``preconstruction`` on a house that has
    authored no permits or locates has nothing in it, stays ``not_started`` for ever, and
    would otherwise be the answer to "where am I" until the day the house was finished.
    """
    occupied = [i for i, m in enumerate(milestones) if m.visits or m.inspections]
    for index, milestone in enumerate(milestones):
        if milestone.state != "done" and index in occupied:
            return milestone.id
    # Everything with anything in it is done. The answer is the next row along, not the
    # empty one at the front of the list.
    start = (occupied[-1] + 1) if occupied else 0
    for milestone in milestones[start:]:
        if milestone.state != "done":
            return milestone.id
    return milestones[-1].id if milestones else ""

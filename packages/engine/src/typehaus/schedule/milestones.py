"""The five states a house passes through, as contiguous slices of the trade order.

A milestone is the unit an owner-builder actually thinks in — "I need to be weathertight
before November" — and it is the only grouping on the board coarse enough to answer "where
am I". It is engine-generic: the slices are over ``emit.trades.CONSTRUCTION_SEQUENCE``, so
a jurisdiction contributes its inspections and nothing else.

Deliberately no dates and no order beyond the trade order that already exists. A milestone
is *done* when every visit in it is done, not when a date passes.

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
    ("foundation", "Foundation", ("earth", "concrete", "drainage")),
    ("weathertight", "Weathertight", ("framing", "floors", "roof", "walls", "openings")),
    ("rough_ins", "Rough-ins", ("plumbing", "electrical", "mechanical")),
    ("insulated", "Insulated and closed up", ()),
    ("final", "Final", ("stairs", "furniture")),
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


def build_milestones(visits: Any, inspections: Any) -> tuple[Milestone, ...]:
    """Fill the five rows with the visits and inspections that landed in each.

    ``state`` is derived from the visits alone: ``done`` when every visit in the milestone
    is done or verified, ``in_progress`` when any has moved off ``todo``. An empty
    milestone is ``not_started`` and stays there — claiming ``done`` for a row with nothing
    in it would mark a house weathertight because nobody had authored any walls.
    """
    by_milestone_visits: dict[str, list[str]] = {name: [] for name in MILESTONE_IDS}
    by_milestone_inspections: dict[str, list[str]] = {name: [] for name in MILESTONE_IDS}
    statuses: dict[str, list[str]] = {name: [] for name in MILESTONE_IDS}
    for visit in visits:
        name = visit.milestone or MILESTONE_OF_TRADE.get(visit.trade, MILESTONE_IDS[0])
        by_milestone_visits[name].append(visit.slug)
        statuses[name].append(visit.status)
    for record in inspections:
        by_milestone_inspections.setdefault(
            record.milestone if hasattr(record, "milestone") else MILESTONE_IDS[0], []
        ).append(record.id)

    out: list[Milestone] = []
    for name, label, trades in MILESTONE_SPECS:
        seen = statuses[name]
        if seen and all(status in ("done", "verified") for status in seen):
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
    """The one to expand on the board: the first that is not done."""
    for milestone in milestones:
        if milestone.state != "done":
            return milestone.id
    return milestones[-1].id if milestones else ""

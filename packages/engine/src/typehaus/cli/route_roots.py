"""Where a proposed run TIES IN — the root end of every route the CLI asks for.

Four questions, one module, because they are the same question asked of four topologies:
a drain lands at an invert on the run it discharges to (:func:`_discharge`); a branch lands
on the nearest main passing its own floor (:func:`_nearest_main`); a branch vent lands on
the chase it shares with its siblings, anywhere along any of them (:func:`_vent_siblings`);
and a supply branch tees onto the trunk that feeds it, anywhere along THAT
(:func:`_supply_trunk`). Split out of ``route_support`` when that file crossed the 500-line
rule in ``AGENTS.md``.

**Supply is the mirror of a vent and it arrived last for a reason.** Until 2026-09-19 a
supply run fell through to ``_vent_siblings``, which takes ``path[-1]`` as the root and
demands another run of the same system whose FIRST OR LAST vertex lands within 3". Both
halves are wrong in mirror image: a supply branch is authored tie-first, so its ``path[0]``
is the tee and its ``path[-1]`` is the riser at the fixture; and a tee sits on a SEGMENT,
which no endpoint-to-endpoint tolerance can find. Every supply target got a refusal about a
vent chase that is not true of a trunk.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel


#: Two vents landing this close to one station are landing on the same thing. The plan grid
#: this repo authors on is a sixteenth of an inch; three inches is the joint tolerance every
#: other trade reading uses (``resolve/mep_soffit.DUCT_JOINT_TOLERANCE_M``) and is reused
#: here so "these two share a chase" means one thing across the engine.
_CHASE_TOLERANCE_M = 3 * 0.0254


def _vent_siblings(model: ResolvedModel, run: Any, problems: list[str]
                   ) -> tuple[tuple[float, float, float], list[str],
                              tuple[tuple[tuple[float, float], ...], ...]] | None:
    """``(the chase station, the siblings, their polylines)`` for a branch vent.

    The root is the run's own downstream end — the station it already lands on — and the
    goal set is that station plus every OTHER vent of this model that lands on it too. A
    branch vent may join any of them anywhere along its length; that is a common vent, and
    it is what ``--tree`` has always done for drains and no mode has ever done for vents.

    The siblings go into ``touch`` as well as into the goals: a run the proposal is meant to
    land ON may not also be a hard prism sitting exactly where the tie is.
    """
    end = (run.path[-1][0], run.path[-1][1])
    root = (end[0], end[1], run.z_m[-1])
    siblings: list[str] = []
    paths: list[tuple[tuple[float, float], ...]] = []
    for other in model.pipe_runs:
        if other.tag == run.tag or other.system != run.system or len(other.path) < 2:
            continue
        if min(((p[0] - end[0]) ** 2 + (p[1] - end[1]) ** 2) ** 0.5
               for p in (other.path[0], other.path[-1])) > _CHASE_TOLERANCE_M:
            continue
        siblings.append(other.tag)
        paths.append(tuple((p[0], p[1]) for p in other.path))
    if not siblings:
        problems.append(
            f"{run.tag}: nothing downstream of it is derivable and no other {run.system} "
            "run lands where it does, so there is nowhere to tie into. Name a --via, or "
            "route the parent first")
        return None
    return root, siblings, tuple(paths)


def _discharge(model: ResolvedModel, run: Any, problems: list[str]
               ) -> tuple[tuple[float, float, float], list[str],
                          tuple[tuple[float, float], ...]] | None:
    """``(root point, the whole downstream chain, the parent's plan polyline)``, or None.

    The chain, not just the parent, and that is what makes a tie reachable at all: a
    branch's root vertex usually sits ON its parent, and its parent's root sits on the
    GRANDparent, so leaving the rest of the chain hard walls the route off from the tie it
    is being routed to. ``drain_tie_ins`` derives the topology from the geometry and this
    walks it to the bottom.
    """
    from typehaus.resolve.mep_queries import drain_tie_ins

    ties = drain_tie_ins([r for r in model.pipe_runs if r.system == run.system])
    parent = ties.get(run.tag)
    if parent is None:
        problems.append(f"{run.tag}: nothing downstream of it is derivable, so there is "
                        "no root to route to. Name a --via, or route the parent first")
        return None
    chain: list[str] = []
    cursor: str | None = parent
    while cursor is not None and cursor not in chain:
        chain.append(cursor)
        cursor = ties.get(cursor)
    other = next(r for r in model.pipe_runs if r.tag == parent)
    z = other.z_m or ()
    if len(z) != len(other.path):
        problems.append(f"{run.tag}: its discharge {parent} carries no resolved "
                        "elevations, so there is no invert to tie into")
        return None
    index = min(range(len(other.path)), key=lambda i: z[i])
    # The min-z vertex is the root a FALLING run needs: a drain arrives at an invert, and
    # that is one elevation at one point. It is also all a vent used to get, which is why a
    # branch vent could never be proposed into the middle of a sibling — the parent's whole
    # line comes back beside it and the caller picks by ``falls``.
    return ((other.path[index][0], other.path[index][1], z[index]), chain,
            tuple((p[0], p[1]) for p in other.path))


def _nearest_main(model: ResolvedModel, point: tuple[float, float], floor_m: float,
                  problems: list[str], target: str, *, exclude: str | None = None
                  ) -> tuple[tuple[float, float, float], str] | None:
    """The nearest drain run's vertex on this fixture's own floor.

    The vertical gate is ``mep.fixture_drain_reach``'s: a run counts only where it passes
    within two feet below and six inches above the fixture's storey datum. Without it the
    nearest main is whatever happens to lie beneath, two storeys down.

    **A run that already serves this fixture is excluded**, and that is not a nicety: asking
    for a branch to a fixture that has one means asking for a REPLACEMENT, and routing to
    the run being replaced finds its own start and reports a negative feasible slope — a
    true statement about a question nobody asked.
    """
    best = None
    for run in model.pipe_runs:
        if run.system != "drain" or not run.z_m:
            continue
        if exclude is not None and exclude in run.serves:
            continue
        for (x, y), z in zip(run.path, run.z_m, strict=False):
            if not (floor_m - 2.0 * 0.3048 <= z <= floor_m + 0.5 * 0.3048):
                continue
            distance = ((x - point[0]) ** 2 + (y - point[1]) ** 2) ** 0.5
            if best is None or distance < best[0]:
                best = (distance, (x, y, z), run.tag)
    if best is None:
        problems.append(f"{target}: no drain run passes on this fixture's own floor, so "
                        "there is nothing to route it to")
        return None
    return (best[1], best[2])


def _supply_trunk(model: ResolvedModel, run: Any, problems: list[str]
                  ) -> tuple[tuple[float, float, float], list[str],
                             tuple[tuple[tuple[float, float, float], ...], ...]] | None:
    """``(a point on the feeder, the whole chain to the source, its plan polyline with z)``.

    The chain rather than the parent alone, for ``_discharge``'s reason: a branch's tee sits
    ON its parent and its parent's tee sits on the GRANDparent, so leaving the rest of the
    chain hard walls the route off from the tie it is being routed to.

    **The polyline carries a z per vertex, and a vent's does not.** A vent chase is vertical,
    so one elevation describes the whole goal line; a supply trunk rises at both ends and
    runs level between, and seeding one z along it would put goals on the trunk's plan line
    at a height the trunk is nowhere near.

    A refusal here names WHICH of the three real causes applies, out of the record
    ``supply_tie_in_records`` already carries. Each is that record read back, which is the
    point of making it a record rather than a dict.
    """
    from typehaus.resolve.mep_ports import placed_ports
    from typehaus.resolve.mep_tie_ins import supply_tie_in_records

    records = {rec.child: rec for rec in supply_tie_in_records(model.pipe_runs,
                                                               placed_ports(model))}
    record = records.get(run.tag)
    ties = {tag: rec.parent for tag, rec in records.items() if rec.parent}
    if record is None or record.parent is None:
        problems.append(_supply_refusal(run, record))
        return None
    chain: list[str] = []
    cursor: str | None = record.parent
    while cursor is not None and cursor not in chain:
        chain.append(cursor)
        cursor = ties.get(cursor)
    parent = next(r for r in model.pipe_runs if r.tag == record.parent)
    z = parent.z_m or ()
    if len(z) != len(parent.path):
        problems.append(f"{run.tag}: its feeder {record.parent} carries no resolved "
                        "elevations, so there is no line to tee onto")
        return None
    line = tuple((p[0], p[1], zz) for p, zz in zip(parent.path, z, strict=False))
    # The root POINT is the derived tee itself — the station the record names — so a
    # refusal, a report and a `--json` payload all say the same place. The whole line goes
    # beside it as the goal SET, and `falls=False` means the caller uses the line.
    root = (record.station[0], record.station[1], run.z_m[0])
    return root, chain, (line,)


def _supply_refusal(run: Any, record: Any) -> str:
    """The sentence a parentless supply run gets, naming which cause applies.

    Three different facts about the model want three different sentences. One about a vent
    chase — which is what every supply run got until 2026-09-19 — is false about all three.
    """
    head = f"{run.tag}: "
    if record is None:
        return (head + "it carries no resolved elevations, so there is no tee to derive")
    inches = None if record.z_gap_m is None else record.z_gap_m * 39.3700787
    if record.reason == "equipment_port":
        return (head + f"it leaves {record.port}, an equipment port, so its source is the "
                "machine and there is no run to tee onto. Route it with --via")
    if record.reason == "cross_system":
        return (head + f"the run standing at its first vertex is {record.nearest}, which is "
                f"a {'different' if record.nearest else 'cross-system'} system. Its source "
                "is a machine rather than a pipe — a water heater, a softener, a mixing "
                "valve — and this derivation names runs. Route it with --via, or route the "
                "run it leaves")
    if record.reason == "elevation":
        return (head + f"{record.nearest} passes under its first vertex but {abs(inches):.1f}\" "
                f"{'above' if inches > 0 else 'below'} it. The riser that would feed this "
                "run is not modelled, which is a gap in the plan and not a lane the search "
                "can find")
    return (head + "no run of any system passes under its first vertex, so the thing that "
            "feeds it is not a run in this model — a service lateral, or a riser nobody "
            "drew. Author it, or name a --via")

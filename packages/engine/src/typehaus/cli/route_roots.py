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

from functools import partial
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel


#: Two vents landing this close to one station are landing on the same thing. The plan grid
#: this repo authors on is a sixteenth of an inch; three inches is the joint tolerance every
#: other trade reading uses (``resolve/mep_soffit.DUCT_JOINT_TOLERANCE_M``) and is reused
#: here so "these two share a chase" means one thing across the engine.
_CHASE_TOLERANCE_M = 3 * 0.0254


#: How far a branch vent's end may stand from its stack and still be tied to it. The two
#: risers of catlin's bundle are 4.8" apart, so this reaches the station the chase point is
#: authored at and not a stack in the next room.
_STACK_REACH_M = 0.3048

#: How far above a vent's highest vertex the stack is offered as a goal: room to rise over
#: a duct bank at the chase and no more.
_STACK_HEADROOM_M = 0.6096


def _vent_siblings(model: ResolvedModel, run: Any, problems: list[str]
                   ) -> tuple[tuple[float, float, float], list[str],
                              tuple[tuple[tuple[float, float, float], ...], ...]] | None:
    """``(the tie point, the siblings, their polylines with z)`` for a branch vent.

    **The root is the STACK** (2026-09-23): the ``VentRun`` riser of this run's own system
    nearest its downstream end — see :func:`_stack_leg`. It used to be the run's own end,
    which on catlin is the chase point between the radon and vent risers, inside both; a
    vent routed there was a vent tied into the radon pipe. The riser of any other system
    stays a hard prism. With no stack in reach, the run's own end is the root, as before.

    The goal set is that tie plus every OTHER vent of this model that lands on it too. A
    branch vent may join any of them anywhere along its length; that is a common vent, and
    it is what ``--tree`` has always done for drains and no mode has ever done for vents.
    The lines carry z, so a vent cannot "arrive" on a sibling's plan line a storey away.

    The siblings and the stack go into ``touch`` as well as into the goals: a run the
    proposal is meant to land ON may not also be a hard prism sitting exactly where the tie
    is.
    """
    end = (run.path[-1][0], run.path[-1][1])
    root = (end[0], end[1], run.z_m[-1])
    siblings: list[str] = []
    paths: list[tuple[tuple[float, float, float], ...]] = []
    stack = _stack_leg(model, run)
    if stack is not None:
        tag, leg, root = stack
        siblings.append(tag)
        paths.append(leg)
    # Only the sibling legs this vent can reach rising: every goal vertex is also a lattice
    # level, and a sibling's whole profile made PR-S-BATH1-VENT's lattice ten levels deep.
    low, high = min(run.z_m), max(run.z_m) + _STACK_HEADROOM_M
    for other in model.pipe_runs:
        if other.tag == run.tag or other.system != run.system or len(other.path) < 2:
            continue
        if min(((p[0] - end[0]) ** 2 + (p[1] - end[1]) ** 2) ** 0.5
               for p in (other.path[0], other.path[-1])) > _CHASE_TOLERANCE_M:
            continue
        # A common vent only into one at least this size: catlin's 2" bath-group vent was
        # proposed into the 1 1/2" kitchen vent, which carries one sink.
        if (other.diameter_m or 0.0) + 1e-9 < (run.diameter_m or 0.0):
            continue
        siblings.append(other.tag)
        if not other.z_m or len(other.z_m) != len(other.path):
            paths.append(tuple((p[0], p[1]) for p in other.path))
            continue
        points = [(p[0], p[1], z) for p, z in zip(other.path, other.z_m, strict=False)]
        paths.extend((a, b) for a, b in zip(points, points[1:], strict=False)
                     if min(a[2], b[2]) <= high and max(a[2], b[2]) >= low)
    if not siblings:
        problems.append(
            f"{run.tag}: nothing downstream of it is derivable and no other {run.system} "
            "run lands where it does, so there is nowhere to tie into. Name a --via, or "
            "route the parent first")
        return None
    return root, siblings, tuple(paths)


def _stack_leg(model: ResolvedModel, run: Any
               ) -> tuple[str, tuple[tuple[float, float, float], ...],
                          tuple[float, float, float]] | None:
    """``(riser tag, the leg it is met on, the tie point)`` for the stack a vent ends at.

    The ``VentRun`` riser whose system is this run's, and of its legs the one nearest the
    run's end in plan that spans the end's elevation. The tie point is on that leg at the
    end's elevation — on a vertical leg, the riser's own station.
    """
    from typehaus.resolve.mep_envelopes import vent_risers
    from typehaus.resolve.mep_soffit import plan_distance_to_segment

    end, z_end = (run.path[-1][0], run.path[-1][1]), run.z_m[-1]
    best = None
    for tag, path, z, _diameter in vent_risers(model):
        if tag.rsplit("-", 1)[-1] != str(run.system):
            continue
        for i in range(len(path) - 1):
            low, high = sorted((z[i], z[i + 1]))
            if not low - _CHASE_TOLERANCE_M <= z_end <= high + _CHASE_TOLERANCE_M:
                continue
            distance, t = plan_distance_to_segment(end, path[i], path[i + 1])
            if distance > _STACK_REACH_M or (best is not None and distance >= best[0]):
                continue
            x = path[i][0] + t * (path[i + 1][0] - path[i][0])
            y = path[i][1] + t * (path[i + 1][1] - path[i][1])
            tie_z = (min(max(z_end, low), high) if path[i] == path[i + 1]
                     else z[i] + t * (z[i + 1] - z[i]))
            leg = ((*path[i], z[i]), (*path[i + 1], z[i + 1]))
            if path[i] == path[i + 1]:
                # A stack runs three storeys; offering all of it seeds lattice levels in the
                # basement and the attic. The vent may meet it from its own lowest point up
                # to _STACK_HEADROOM_M over its current tie, to rise over something.
                top = min(high, max(run.z_m) + _STACK_HEADROOM_M)
                leg = ((*path[i], max(low, min(min(run.z_m), top))), (*path[i], top))
            best = (distance, tag, leg, (x, y, tie_z))
    return None if best is None else best[1:]


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
    """``(a point on the feeder, the whole chain to the source, its plan polyline with z)``,
    or ``(the port, [], ())`` for a trunk that leaves an equipment port.

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

    ports = placed_ports(model)
    records = {rec.child: rec for rec in supply_tie_in_records(model.pipe_runs, ports)}
    record = records.get(run.tag)
    ties = {tag: rec.parent for tag, rec in records.items() if rec.parent}
    if record is not None and record.reason == "equipment_port":
        # A trunk leaving a machine roots ON the port: one exact point, no line to tee onto.
        port = next((p for p in ports
                     if f"{p.equipment_tag}.{p.port_tag}" == record.port), None)
        if port is not None:
            return port.point, [], ()
        problems.append(f"{run.tag}: it leaves {record.port}, an equipment port that could "
                        "not be placed, so there is no point to root it on. Route it with "
                        "--via")
        return None
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


def _supply_children(model: ResolvedModel, run: Any) -> tuple[str, ...]:
    """The runs that tee off ``run`` — their tie points ride on its line."""
    from typehaus.resolve.mep_ports import placed_ports
    from typehaus.resolve.mep_tie_ins import supply_tie_in_records

    return tuple(rec.child for rec in supply_tie_in_records(model.pipe_runs,
                                                            placed_ports(model))
                 if rec.parent == run.tag)


def _supply_refusal(run: Any, record: Any) -> str:
    """The sentence a parentless supply run gets, naming which cause applies.

    Three different facts about the model want three different sentences. One about a vent
    chase — which is what every supply run got until 2026-09-19 — is false about all three.
    """
    head = f"{run.tag}: "
    if record is None:
        return (head + "it carries no resolved elevations, so there is no tee to derive")
    inches = None if record.z_gap_m is None else record.z_gap_m * 39.3700787
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


def hold_upstream(model: ResolvedModel, ends: Any, target: str, count: int,
                  problems: list[str]) -> Any:
    """``ends`` with its origin moved to vertex ``count`` of the run, and the vertices
    before it kept as authored — ``--hold-upstream``.

    A vent is pinned at its fixture end by the wet-wall legs it ``serves`` through, and a
    search from the fixture is free to drop them: on catlin one ``PR-M-WC-VENT`` alternative
    did. ``--via`` cannot pin them — it only adds lattice lines at the root's elevation — so
    this starts the search where the held legs end. None, with a reason, when it cannot.
    """
    from dataclasses import replace

    run = next((r for r in model.pipe_runs if r.tag == target), None)
    if run is None or ends.tie_is_the_goal:
        problems.append(f"{target}: --hold-upstream holds the upstream legs of a drain or "
                        "vent run, and this is not one")
        return None
    if not 0 < count < len(run.path) - 1:
        problems.append(f"{target}: --hold-upstream {count} leaves nothing to route; it "
                        f"has {len(run.path)} vertices")
        return None
    points = [(p[0], p[1], z) for p, z in zip(run.path, run.z_m, strict=False)]
    return replace(ends, origin=points[count], held=tuple(points[:count]))


def search_for(model: ResolvedModel, graph: Any, ends: Any, slope: float | None):
    """``(search, refusal report)`` — the plain A* for a pressurised run, the sloped one for
    a drain.

    **This is where "search flat, slope after" ends.** A drain's invert is a function of
    developed length alone, so putting the developed length in the search state makes every
    constraint on its height testable where it can steer the lane rather than only refuse it
    afterwards. See ``routing/gravity_search.py`` and the drain note's §8, where the cheap
    lane passes a head budget taken at the goal and is a quarter of an inch under a truss
    web at its third bend.

    The returned callable has ``shortest_route``'s exact signature so
    ``alternatives.alternative_routes`` takes either without knowing which. A vent or a
    radon pipe gets ``shortest_route(rising=True)``: it may never lose elevation on the way
    to its root (``routing/trades/pipe.rises``).

    Moved here from ``cmd_route`` when that file passed the 500-line rule.
    """
    from typehaus.routing.gravity import minimum_slope
    from typehaus.routing.gravity_search import (
        GravityProblem,
        GravityRefusal,
        member_constraints,
        sloped_route,
    )
    from typehaus.routing.search import shortest_route
    from typehaus.routing.trades.pipe import rises

    if not ends.falls:
        if ends.kind == "pipe" and rises(str(ends.system)):
            return partial(shortest_route, rising=True), None
        return shortest_route, None

    report = GravityRefusal()
    # The band this run can possibly occupy: its tie at the bottom, its start ceiling at the
    # top. Without it every floor in the model constrains every run — see
    # ``member_constraints`` — and a second-floor branch is refused against a basement joist.
    band = (min(ends.origin[2], ends.root[2]), max(ends.origin[2], ends.root[2]))
    constraints = member_constraints(model, graph, band)
    grade = slope if slope is not None else minimum_slope(ends.diameter_m)

    def search(a_graph, a_space, start, goals):
        problem = GravityProblem(
            ceiling_m=ends.origin[2], grade_in_per_ft=grade,
            diameter_m=ends.diameter_m,
            required_m=dict.fromkeys(goals, ends.root[2]))
        return sloped_route(a_graph, a_space, start, goals, problem,
                            constraints=constraints, refusal=report)

    return search, report

"""Tie-in derivation and trade-specific search selection for haus route.

Drains target downstream inverts; vents target same-system stacks/siblings; supply
branches target feeder segments with their own elevations. See docs/routing.md."""

from __future__ import annotations

from dataclasses import replace
from functools import partial
from typing import TYPE_CHECKING, Any

from typehaus.cli.route_supply_roots import (  # supply roots, split out; re-exported
    _supply_children,
    _supply_refusal,
    _supply_trunk,
    reroot_supply,
    supply_records,
)
from typehaus.hardware.plan_geometry import distance_point_to_segment

__all__ = ["_supply_children", "_supply_refusal", "_supply_trunk", "reroot_supply",
           "supply_records"]

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
        # Either end on this run's tie, or this run's tie ON it: a branch vent tees into its
        # parent mid-leg, which is what `mep.vent_reachability` accepts (2026-09-24).
        if min(((p[0] - end[0]) ** 2 + (p[1] - end[1]) ** 2) ** 0.5
               for p in (other.path[0], other.path[-1])) > _CHASE_TOLERANCE_M and min(
                distance_point_to_segment(end, a, b)
                for a, b in zip(other.path, other.path[1:], strict=False)
        ) > _CHASE_TOLERANCE_M:
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
    if getattr(run, "sanitary", True) is False:
        # Indirect waste lands where it was authored to, not at the chain's lowest vertex:
        # PR-M-COND-HEADS' parent ends in an air gap 78" lower, a second line to build.
        point = _landing(run, other, z)
        return (point, chain, tuple((p[0], p[1]) for p in other.path))
    index = min(range(len(other.path)), key=lambda i: z[i])
    # The min-z vertex is the root a FALLING run needs: a drain arrives at an invert, and
    # that is one elevation at one point. It is also all a vent used to get, which is why a
    # branch vent could never be proposed into the middle of a sibling — the parent's whole
    # line comes back beside it and the caller picks by ``falls``.
    return ((other.path[index][0], other.path[index][1], z[index]), chain,
            tuple((p[0], p[1]) for p in other.path))


def _landing(run: Any, parent: Any, z: Any) -> tuple[float, float, float]:
    """The point on ``parent``'s polyline nearest ``run``'s last vertex, at its invert there.

    Invert is linear in plan length between the parent's vertices, the reading
    ``resolve/mep_slope`` gives an authored grade (condensate basis §3)."""
    from typehaus.resolve.mep_soffit import plan_distance_to_segment

    end = (run.path[-1][0], run.path[-1][1])
    best = None
    for i in range(len(parent.path) - 1):
        a, b = parent.path[i], parent.path[i + 1]
        distance, t = plan_distance_to_segment(end, a, b)
        if best is None or distance < best[0]:
            best = (distance, (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]),
                               z[i] + t * (z[i + 1] - z[i])))
    return best[1] if best is not None else (end[0], end[1], z[0])


def sump_endpoints(model: ResolvedModel, run: Any, problems: list[str]
                   ) -> tuple[tuple[float, float, float], str] | None:
    """``(tie point, the riser's tag)`` for a pump's discharge line.

    The pump names its line (``SumpPump.discharge_line_ref``) and what it empties into
    (``discharge``); a leader's buried extension has a derived riser,
    ``<discharge>-EXT-RISER`` (``resolve/drainage``). The tie is the riser's plan centre at the
    line's own authored end elevation, clamped onto the column (a pressure wye has no grade to
    solve). Else None with the cause, the element and the fix: a line to "daylight" or a
    drywell has no column to root on."""
    sump = next((e for e in model.plan.all_elements()
                 if getattr(getattr(e, "pump", None), "discharge_line_ref", None) == run.tag),
                None)
    if sump is None:
        problems.append(f"{run.tag}: no sump pump names it as its discharge_line_ref, so "
                        "its destination is not derivable. Set SumpPump.discharge_line_ref "
                        f"to {run.tag} on the pit it serves")
        return None
    receiver = sump.pump.discharge
    riser = next((s for s in model.solids if s.tag == f"{receiver}-EXT-RISER"), None)
    if riser is None:
        problems.append(
            f"{run.tag}: its pump {sump.tag} discharges to {receiver!r}, which has no "
            f"modelled vertical ({receiver}-EXT-RISER) to tie onto, so no root is derivable. "
            "Give the receiver a buried extension (Downspout.extension) or route with --via")
        return None
    xs = [p[0] for p in riser.outline]
    ys = [p[1] for p in riser.outline]
    x, y = sum(xs) / len(xs), sum(ys) / len(ys)
    z = min(max(run.z_m[-1], riser.z0_m), riser.z1_m)
    return (x, y, z), str(riser.tag)


def sleeve_hold(model: ResolvedModel, run: Any
                ) -> tuple[int, str, float] | None:
    """``(vertex the tail starts at, sleeve tag, plan distance m)`` for the cast sleeve ``run``
    is authored through, or None.

    Found by geometry: a horizontal sleeve whose centre lies within its own bore of a leg of
    the authored polyline, at that leg's elevation (a vertical leg has no plan extent and
    passes none). The legs up to and through it are held, as ``hold_upstream`` holds legs: a
    lattice via only seeds nodes and cannot force a crossing. The tail starts at the first
    vertex past the sleeve, which must stand outside the wall that hosts it."""
    from typehaus.resolve.mep_soffit import plan_distance_to_segment

    best = None
    for sleeve in model.sleeves:
        if sleeve.axis != "horizontal" or sleeve.center_z_m is None:
            continue
        for i in range(len(run.path) - 1):
            distance, t = plan_distance_to_segment(sleeve.center, run.path[i], run.path[i + 1])
            z = run.z_m[i] + t * (run.z_m[i + 1] - run.z_m[i])
            if (distance <= sleeve.sleeve_d_m / 2.0 and run.path[i] != run.path[i + 1]
                    and abs(z - sleeve.center_z_m) <= sleeve.sleeve_d_m
                    and (best is None or distance < best[2])):
                best = (i + 1, sleeve.tag, distance)
    return best


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


def hold_upstream(model: ResolvedModel, ends: Any, target: str, count: int,
                  problems: list[str]) -> Any:
    """``ends`` with ``count`` authored legs at the search origin kept and the search
    started where they end — ``--hold-upstream``. None, with a reason, when it cannot.

    A vent is pinned at its fixture end by the wet-wall legs it ``serves`` through, and a
    search from the fixture is free to drop them (one ``PR-M-WC-VENT`` alternative did);
    ``--via`` only adds lattice lines at the root's elevation. A supply searches from its
    fixture too, so its last ``count`` legs are held: the tail a branch tees on (``--lift``,
    PR-M-DW-HW on PR-B-HW-KITCH's riser). ``one_proposal`` appends them after the reversal.
    """
    run = next((r for r in model.pipe_runs if r.tag == target), None)
    if run is None:
        problems.append(f"{target}: --hold-upstream holds an authored pipe run's legs, and "
                        "this is not one")
        return None
    if not 0 < count < len(run.path) - 1:
        problems.append(f"{target}: --hold-upstream {count} leaves nothing to route; it "
                        f"has {len(run.path)} vertices")
        return None
    points = [(p[0], p[1], z) for p, z in zip(run.path, run.z_m, strict=False)]
    if ends.tie_is_the_goal:
        return replace(ends, origin=points[-1 - count], held=tuple(points[-count:]),
                       origin_lead=None)
    return replace(ends, origin=points[count], held=tuple(points[:count]), origin_lead=None)


def search_for(model: ResolvedModel, graph: Any, ends: Any, slope: float | None):
    """Return (search callable, refusal report) with shortest_route's signature.

    Drains carry developed length and legal start-elevation bands in gravity_search's labels,
    so constraints steer the lane at their crossing station (drain oracle §8). Pressurised
    runs use plain A*; vent/radon searches use rising=True and may never lose elevation."""
    from typehaus.cli.route_fixture_vent import arm_problem
    from typehaus.routing.fitting_room import fitting_terms
    from typehaus.routing.gravity import CONDENSATE_LADDER, graded_route, minimum_slope
    from typehaus.routing.gravity_band import (
        band_obstacles,
        member_constraints,
        terminal_pardons,
    )
    from typehaus.routing.gravity_search import GravityProblem, GravityRefusal, sloped_route
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
    band = (min(ends.weir, ends.root[2]), max(ends.origin[2], ends.root[2]))
    constraints = member_constraints(model, graph, band)
    grade = slope if slope is not None else minimum_slope(
        ends.diameter_m, sanitary=bool(ends.echo.get("sanitary", True)))
    ladder = CONDENSATE_LADDER if slope is None and not ends.echo.get("sanitary", True) \
        else None

    def search(a_graph, a_space, start, goals):
        tied = len(goals)
        goals = _spaced_goals(model, a_graph, goals, ends, report)
        nipple, heel = fitting_terms(a_space.cost, "drain", ends.diameter_m,
                                     ends.echo.get("material"), ends.radius_m)
        problem = GravityProblem(
            ceiling_m=ends.weir, grade_in_per_ft=grade,
            diameter_m=2.0 * ends.radius_m,
            required_m=dict.fromkeys(goals, ends.root[2]), nipple_m=nipple, heel_m=heel)
        heights = {**dict.fromkeys(goals, ends.root[2]), start: ends.weir}
        obstacles = band_obstacles(a_space, a_graph,
                                   terminal_pardons(a_space, a_graph, heights, start),
                                   start)
        arm, vent = arm_problem(model, ends, a_graph, a_space, start, goals, grade,
                                obstacles, report, constraints)
        wet = arm.pop("wet", {})
        if wet:  # a wet-vent join is a goal at the drain's own centreline there
            goals = goals | set(wet)
            arm["required_m"] = {**problem.required_m,
                                 **{n: tie.join[2] for n, tie in wet.items()}}
        if not goals:  # every tie spaced out: a refusal naming the inlet, not a search
            report.notes.append(f"{ends.fixture or ends.system}: all {tied} tie(s) were "
                                "spaced out, so no goal is left to route to")
            return None
        if arm:
            problem = replace(problem, **arm)
        found = graded_route(
            lambda p: sloped_route(a_graph, a_space, start, goals, p, constraints=constraints,
                                   refusal=report, obstacles=obstacles),
            problem, ladder)
        if found is not None and found.takeoff is not None:
            found.vent, found.wet = vent, wet.get(found.takeoff)
        return found

    return search, report


def _spaced_goals(model: ResolvedModel, graph: Any, goals: set[int], ends: Any,
                  report: Any) -> set[int]:
    """Goals on a level main that keep the wye-to-wye pitch from every inlet on it (§10).

    A vertical barrel's stack pitch stays with ``mep.drain_inlet_spacing``. An emptied set is
    returned empty, with a note naming the inlet, so the refusal says what crowded it.
    """
    from typehaus.resolve.mep_inlet_spacing import level_inlets, main_inlet_pitch_m

    inlets = level_inlets(model.pipe_runs, frozenset(ends.touch))
    pitch = main_inlet_pitch_m(ends.diameter_m)
    if not inlets or pitch is None:
        return goals
    kept, crowded = set(), None
    for goal in goals:
        node = graph.nodes[goal]
        near = next((tag for x, y, z, tag in inlets
                     if abs(z - node.z) < pitch and abs(x - node.x) + abs(y - node.y)
                     < pitch - 1e-6), None)
        if near is None:
            kept.add(goal)
        else:
            crowded = near
    if not kept and crowded is not None:
        report.notes.append(f"every tie on {crowded} is within {pitch / 0.0254:.3f}\" of an "
                            "inlet already on it (two wyes cannot stack closer)")
    return kept
